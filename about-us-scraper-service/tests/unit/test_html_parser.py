import pytest
from unittest.mock import Mock, patch
from requests.exceptions import HTTPError
from api.services.html_parser import extract_media_from_html


@pytest.fixture
def mock_response():
    """Create a mock response with HTML content."""
    response = Mock()
    response.text = """
    <html>
        <body>
            <img src="image1.jpg" alt="First image">
            <img src="image2.jpg" title="Second image">
            <div>
                <img src="image3.jpg">Some context text</div>
            <div>
                <img src="image4.jpg">
            </div>
            <video src="video1.mp4" title="First video"></video>
            <iframe src="video2.mp4"></iframe>
        </body>
    </html>
    """
    return response


def test_extract_media_success(mock_response):
    """Test successful media extraction."""
    with patch("requests.get", return_value=mock_response):
        media = extract_media_from_html("https://example.com")

    assert len(media) == 6

    # Check images
    assert ("https://example.com/image1.jpg", "image", "First image") in media
    assert ("https://example.com/image2.jpg", "image", "Second image") in media
    assert ("https://example.com/image3.jpg", "image", "Some context text") in media
    assert ("https://example.com/image4.jpg", "image", "Image") in media

    # Check videos
    assert ("https://example.com/video1.mp4", "video", "First video") in media
    assert ("https://example.com/video2.mp4", "video", "Video") in media


def test_extract_media_http_error():
    """Test handling of HTTP errors."""
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = HTTPError("404 Not Found")

    with patch("requests.get", return_value=mock_response):
        with pytest.raises(HTTPError, match="404 Not Found"):
            extract_media_from_html("https://example.com")


def test_extract_media_empty_response():
    """Test handling of empty HTML."""
    mock_response = Mock()
    mock_response.text = "<html><body></body></html>"

    with patch("requests.get", return_value=mock_response):
        media = extract_media_from_html("https://example.com")

    assert len(media) == 0


def test_extract_media_relative_urls(mock_response):
    """Test handling of relative URLs."""
    mock_response.text = """
    <html>
        <body>
            <img src="/images/image1.jpg" alt="First image">
            <img src="../images/image2.jpg" title="Second image">
            <video src="/videos/video1.mp4" title="First video"></video>
        </body>
    </html>
    """

    with patch("requests.get", return_value=mock_response):
        media = extract_media_from_html("https://example.com/page")

    assert len(media) == 3
    assert ("https://example.com/images/image1.jpg", "image", "First image") in media
    assert ("https://example.com/images/image2.jpg", "image", "Second image") in media
    assert ("https://example.com/videos/video1.mp4", "video", "First video") in media


def test_extract_media_missing_src():
    """Test handling of media elements without src attribute."""
    mock_response = Mock()
    mock_response.text = """
    <html>
        <body>
            <img alt="No src">
            <video title="No src"></video>
            <iframe></iframe>
        </body>
    </html>
    """

    with patch("requests.get", return_value=mock_response):
        media = extract_media_from_html("https://example.com")

    assert len(media) == 0


def test_extract_media_data_urls():
    """Test handling of data URLs."""
    mock_response = Mock()
    mock_response.text = """
    <html>
        <body>
            <img src="data:image/png;base64,..." alt="Data URL">
            <img src="https://example.com/image.jpg" alt="Regular URL">
        </body>
    </html>
    """

    with patch("requests.get", return_value=mock_response):
        media = extract_media_from_html("https://example.com")

    assert len(media) == 2
    assert ("data:image/png;base64,...", "image", "Data URL") in media
    assert ("https://example.com/image.jpg", "image", "Regular URL") in media


def test_extract_media_context_truncation():
    """Test context text truncation."""
    mock_response = Mock()
    mock_response.text = (
        """
    <html>
        <body>
            <div>
                <img src="image.jpg">
                """
        + "Very long text " * 50
        + """
            </div>
        </body>
    </html>
    """
    )

    with patch("requests.get", return_value=mock_response):
        media = extract_media_from_html("https://example.com")

    assert len(media) == 1
    assert len(media[0][2]) <= 100  # Context should be truncated


def test_extract_media_special_characters():
    """Test handling of special characters in URLs and context."""
    mock_response = Mock()
    mock_response.text = """
    <html>
        <body>
            <img src="image with spaces.jpg" alt="Text with &amp; and &quot;">
            <img src="image%20with%20encoding.jpg" title="Text with 'quotes'">
        </body>
    </html>
    """

    with patch("requests.get", return_value=mock_response):
        media = extract_media_from_html("https://example.com")

    assert len(media) == 2
    assert (
        "https://example.com/image with spaces.jpg",
        "image",
        'Text with & and "',
    ) in media
    assert (
        "https://example.com/image%20with%20encoding.jpg",
        "image",
        "Text with 'quotes'",
    ) in media
