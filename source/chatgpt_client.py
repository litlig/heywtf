"""ChatGPT web client using Playwright with browser automation."""

from __future__ import annotations

import time
from typing import Generator, TYPE_CHECKING
from source.providers import Provider, ProviderError

if TYPE_CHECKING:
    from playwright.sync_api import Page


# Backward-compatible alias
ChatGPTError = ProviderError


class ChatGPTProvider(Provider):
    """ChatGPT web provider using browser automation."""

    def __init__(self, model: str = "gpt-4o-mini", headless: bool = True):
        """Initialize ChatGPT provider.

        Args:
            model: Ignored; web version uses model selected in UI.
            headless: Whether to run browser in headless mode.
        """
        self.model = model
        self.headless = headless

    def chat_stream(
        self,
        messages: list[dict],
    ) -> Generator[str, None, None]:
        """Automate ChatGPT web to get response, yielding content chunks.

        Args:
            messages: List of message dicts with 'role' and 'content'.

        Yields:
            Content string chunks.

        Raises:
            ProviderError: If browser automation fails.
        """
        # Extract the user message (last message with role 'user')
        user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        if not user_message:
            raise ProviderError("No user message found in messages list")

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ProviderError(
                "Playwright not installed (required for the chatgpt-web backend).\n"
                "Install it:\n"
                "  pip install 'heywtf[chatgpt-web]'\n"
                "  playwright install chromium"
            )

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                page = browser.new_page()

                try:
                    _automate_chatgpt(page, user_message)
                    # Yield the full response
                    response = _extract_response(page)
                    yield response
                finally:
                    browser.close()

        except ProviderError:
            raise
        except Exception as e:
            error_msg = str(e)
            if "Timeout" in error_msg or "timed out" in error_msg:
                raise ProviderError(
                    f"ChatGPT web took too long to load.\n"
                    f"Try one of the following:\n"
                    f"  1. Check your internet connection\n"
                    f"  2. Try again (server may be busy)\n"
                    f"  3. Switch to local Ollama: export BUDDY_BACKEND=ollama\n"
                    f"  4. Verify ChatGPT is accessible: open https://chat.openai.com"
                )
            raise ProviderError(f"ChatGPT web automation failed: {e}")


def _automate_chatgpt(page: Page, prompt: str, timeout: int = 120) -> None:
    """Navigate to ChatGPT, fill prompt, and wait for response.

    Args:
        page: Playwright Page object.
        prompt: The prompt to send to ChatGPT.
        timeout: Seconds to wait for response (default 120).

    Raises:
        ProviderError: If automation fails at any step.
    """
    try:
        # Navigate to ChatGPT with generous timeout (network can be slow)
        # Try with progressively simpler wait conditions if timeout occurs
        page_load_timeout = 90000  # 90 seconds - generous for slow networks
        
        try:
            page.goto("https://chat.openai.com", wait_until="load", timeout=page_load_timeout)
        except Exception as e:
            if "Timeout" in str(e):
                # Network is slow, try with simpler condition
                page.goto("https://chat.openai.com", wait_until="domcontentloaded", timeout=page_load_timeout)
            else:
                raise

        # Wait a moment for the page to fully load and settle
        page.wait_for_timeout(3000)

        # Check if we need to sign in (simple heuristic)
        # If we're logged out, we'll hit the login page
        if page.url.startswith("https://chat.openai.com/auth/"):
            raise ProviderError(
                "Not logged into ChatGPT. Please log in at https://chat.openai.com first."
            )

        # Try to find the message input field using multiple strategies
        input_element = None
        
        # Strategy 1: Look for textarea with common ChatGPT patterns
        for selector in [
            'textarea[placeholder*="Message"]',
            'textarea[id*="prompt"]',
            'textarea',
        ]:
            elements = page.locator(selector).all()
            for elem in elements:
                try:
                    if elem.is_visible() and elem.get_attribute("data-testid") != "send-button":
                        input_element = elem
                        break
                except:
                    pass
            if input_element:
                break
        
        # Strategy 2: Look for contenteditable div
        if not input_element:
            elements = page.locator('div[contenteditable="true"]').all()
            for elem in elements:
                try:
                    if elem.is_visible():
                        # Check it's not the send button
                        if "send" not in (elem.get_attribute("data-testid") or "").lower():
                            input_element = elem
                            break
                except:
                    pass
        
        # If still not found, wait a bit more and try again
        if not input_element:
            page.wait_for_timeout(2000)
            for selector in ['textarea[placeholder*="Message"]', 'textarea', 'div[contenteditable="true"]']:
                try:
                    elem = page.locator(selector).first
                    if elem.is_visible():
                        input_element = elem
                        break
                except:
                    pass
        
        if not input_element:
            raise ProviderError(
                "Could not find ChatGPT message input. "
                "The page layout may have changed or you may not be logged in."
            )

        # Focus on the input and type the prompt
        input_element.click()
        input_element.fill("")
        input_element.type(prompt, delay=5)

        # Look for and click the send button
        # ChatGPT usually has a button with aria-label containing "Send" or a send icon
        send_button = None
        
        for selector in [
            'button[aria-label*="Send"]',
            'button[data-testid*="send"]',
            'button:has-text("Send")',
        ]:
            try:
                elements = page.locator(selector).all()
                for btn in elements:
                    if btn.is_visible() and btn.is_enabled():
                        send_button = btn
                        break
            except:
                pass
            
            if send_button:
                break
        
        # If still not found, look for any enabled button near the input
        if not send_button:
            # Find all visible buttons and check the last one (likely send button)
            buttons = page.locator("button").all()
            for btn in reversed(buttons):
                try:
                    if btn.is_visible() and btn.is_enabled():
                        # Avoid obvious non-send buttons
                        aria_label = btn.get_attribute("aria-label") or ""
                        if "send" in aria_label.lower() or not aria_label:
                            send_button = btn
                            break
                except:
                    pass

        if not send_button:
            raise ProviderError("Could not find ChatGPT send button.")

        # Click send
        send_button.click()

        # Wait for the response to appear
        page.wait_for_selector('div[data-message-id]', timeout=timeout * 1000)

        # Wait a bit more for the response to finish streaming
        _wait_for_response_complete(page, timeout)

    except Exception as e:
        if isinstance(e, ProviderError):
            raise
        raise ProviderError(f"Automation step failed: {e}")


def _wait_for_response_complete(page: Page, timeout: int = 120) -> None:
    """Wait for ChatGPT response to finish streaming.

    Args:
        page: Playwright Page object.
        timeout: Seconds to wait for completion.

    Raises:
        ProviderError: If timeout is exceeded.
    """
    start = time.time()
    last_change = time.time()

    while time.time() - start < timeout:
        try:
            # Get the last message in the conversation
            messages = page.locator('div[data-message-id]').all()
            if not messages:
                time.sleep(0.5)
                continue

            last_message = messages[-1]
            current_text = last_message.inner_text()

            # Check if content is still changing (streaming)
            if time.time() - last_change > 2:  # No change for 2 seconds = done
                return

            time.sleep(0.5)
            new_text = last_message.inner_text()
            if new_text != current_text:
                last_change = time.time()

        except Exception:
            time.sleep(0.5)

    raise ProviderError(f"Timeout waiting for ChatGPT response after {timeout}s")


def _extract_response(page: Page) -> str:
    """Extract the last assistant message from the conversation.

    Args:
        page: Playwright Page object.

    Returns:
        The assistant's response text.

    Raises:
        ProviderError: If response cannot be extracted.
    """
    try:
        # Get all messages
        messages = page.locator('div[data-message-id]').all()
        if not messages:
            raise ProviderError("No messages found in conversation")

        # The last message should be from the assistant
        last_message = messages[-1]
        response_text = last_message.inner_text()

        if not response_text or response_text.isspace():
            raise ProviderError("Received empty response from ChatGPT")

        return response_text

    except Exception as e:
        if isinstance(e, ProviderError):
            raise
        raise ProviderError(f"Failed to extract response: {e}")
