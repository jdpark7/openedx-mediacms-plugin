# MediaCMS Plugin for Tutor

This is a Tutor plugin that integrates the **MediaCMS XBlock** into the Open edX platform. It allows you to embed videos from a MediaCMS instance (or any video URL) with advanced tracking features like:

- **Progress Tracking**: Tracks how much of the video a student has watched.
- **Completion Rules**: Automatically marks the unit as complete when a percentage threshold (default 90%) is reached.
- **Playback Speed**: Standard UI controls for 0.5x, 1x, 1.5x, 2x speeds.
- **Resumable Playback**: Remembers where the student left off.

## Installation

You can install this plugin directly from the source repository.

### 1. Install via pip
Run the following command in your Tutor environment:

```bash
pip install git+https://github.com/jdpark7/openedx-mediacms-plugin.git
```

### 2. Enable the Plugin
Enable the plugin in Tutor:

```bash
tutor plugins enable mediacms
```

### 3. Build & Deploy
Since this plugin injects the XBlock code into the Open edX platform, you must rebuild the Docker image:

```bash
tutor images build openedx
tutor local launch
```

## Usage

### Adding to a Course
1. Go to **Studio** and open your course.
2. Navigate to **Settings** > **Advanced Settings**.
3. In the **Advanced Module List**, add `"mediacms"`.
4. Save the changes.
5. Go to a Unit in your course content.
6. Click **Advanced** component button.
7. Select **MediaCMS Video**.

### Configuring the Video
Click **Edit** on the newly created component to set:
- **Display Name**: Title of the video.
- **Video URL**: Direct URL to the video file (mp4, m3u8, etc.) or MediaCMS embed.
- **Completion Percentage**: The percentage of the video that must be watched to trigger completion (e.g., 90).
