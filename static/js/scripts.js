// This file is intentionally left blank.
document.getElementById('videoInput').addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (file) {
        const videoPlayer = document.getElementById('videoPlayer');
        const videoSource = document.getElementById('videoSource');
        videoSource.src = URL.createObjectURL(file);
        videoPlayer.load();
    }
});