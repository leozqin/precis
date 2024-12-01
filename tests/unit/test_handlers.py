import pytest

from app.handlers import ContentRetrievalHandler, LLMHandler


def test_llm_handler():
    class TestLLMHandler(LLMHandler):
        id = "test_llm_handler"

        def summarize(self, feed, entry, mk):
            return "hello world"

    handler = TestLLMHandler()

    assert isinstance(handler.get_summarization_prompt("hello world"), str)
    assert isinstance(handler.summarization_system_prompt, str)


@pytest.mark.asyncio
async def test_content_retrieval_handler_is_banned():
    fn = ContentRetrievalHandler.is_banned

    assert await fn("reddit.com/abc123")
    assert await fn("http://www.reddit.com/abc123")
    assert not await fn("cnn.com/abc123")
    assert not await fn("https://www.cnn.com/abc123")


def test_content_retrieval_handler_get_main_content():
    fn = ContentRetrievalHandler.get_main_content

    assert fn("hello world")
