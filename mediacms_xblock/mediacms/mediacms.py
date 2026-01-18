"""MediaCMS XBlock logic."""

import pkg_resources
import logging
import requests
import json
import re
from urllib.parse import urlparse, parse_qs

from xblock.core import XBlock
from xblock.fields import Scope, String, Integer, List, Float
from xblock.fragment import Fragment

log = logging.getLogger(__name__)

class MediaCMSXBlock(XBlock):
    """
    XBlock to play videos from a MediaCMS instance and track completion.
    """

    display_name = String(
        display_name="Display Name",
        default="MediaCMS Video",
        scope=Scope.settings,
        help="The name to display for this component."
    )

    mediacms_url = String(
        display_name="MediaCMS URL",
        default="https://deic.mediacms.io/view?m=6ui2LMmEs",
        scope=Scope.settings,
        help="The full URL to the video page on your MediaCMS instance (e.g., http://my-mediacms.site/view?m=TOKEN).",
    )

    completion_percentage = Integer(
        display_name="Completion Percentage",
        default=90,
        scope=Scope.settings,
        help="The percentage of the video that must be watched to trigger completion (0-100)."
    )

    # User state
    progress = Integer(
        default=0,
        scope=Scope.user_state,
        help="Current max progress percentage (0-100)."
    )

    # Store ranges as a list of [start, end] lists for JSON serialization
    watched_ranges = List(
        default=[],
        scope=Scope.user_state,
        help="List of watched time ranges (e.g. [[0, 10], [20, 30]])."
    )

    last_watched_url = String(
        default="",
        scope=Scope.user_state,
        help="The URL of the video for which the current progress is recorded."
    )

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    def _get_media_info(self, url):
        """
        Parse MediaCMS URL and fetch API details.
        Ported from Moodle mod_mediacms lib.php.
        """
        if not url:
            return None

        parsed = urlparse(url)
        token = ""

        # Pattern 1: /watch?v=TOKEN or /view?m=TOKEN
        query = parse_qs(parsed.query)
        if 'v' in query:
            token = query['v'][0]
        elif 'm' in query:
            token = query['m'][0]

        # Pattern 2: /w/TOKEN or /v/TOKEN or /media/TOKEN
        if not token and parsed.path:
            match = re.search(r'/(?:w|v|media)/([a-zA-Z0-9\-_]+)', parsed.path)
            if match:
                token = match.group(1)

        if not token:
            return None

        # Guess base URL
        scheme = parsed.scheme if parsed.scheme else 'http'
        netloc = parsed.netloc
        base_url = f"{scheme}://{netloc}"

        api_url = f"{base_url}/api/v1/media/{token}"

        try:
            response = requests.get(api_url, timeout=5)
            response.raise_for_status()
            data = response.json()
            data['base_url'] = base_url # Attach base_url for later use
            return data
        except Exception as e:
            log.error(f"MediaCMS API fetch failed for {api_url}: {e}")
            return None

    def student_view(self, context=None):
        """
        The primary view of the MediaCMSXBlock, shown to students
        when viewing courses.
        """
        context = context or {}

        # Check for URL change and reset progress immediately (Server-Side Logic)
        if not self.last_watched_url:
             # First time init
             self.last_watched_url = self.mediacms_url
        elif self.mediacms_url != self.last_watched_url:
             # URL changed since last view

             self.progress = 0
             self.watched_ranges = []
             self.last_watched_url = self.mediacms_url
        
        # Prepare context variables
        video_src = self.mediacms_url
        if not video_src:
             video_src = "https://deic.mediacms.io/view?m=6ui2LMmEs" # Fallback if empty in DB
        
        mimetype = "video/mp4" # Fallback
        
        # Only fetch info if we have a real URL and not just a placeholder
        # To avoid API spam in Studio
        info = None
        if video_src:
            info = self._get_media_info(video_src)
        
        if info:
            base_url = info.get('base_url', '')
            
            # Logic ported from view.php to find best source
            # 1. Check for HLS
            if info.get('hls_info') and info['hls_info'].get('master_file'):
                src = info['hls_info']['master_file']
                if not src.startswith('http'):
                    src = f"{base_url}{src}"
                video_src = src
                mimetype = "application/x-mpegURL"
            
            # 2. Check for Encodings (h264)
            elif info.get('encodings_info'):
                # Sort resolutions descending
                resolutions = sorted(info['encodings_info'].keys(), key=lambda x: int(x) if x.isdigit() else 0, reverse=True)
                for res in resolutions:
                    res_info = info['encodings_info'][res]
                    if 'h264' in res_info and 'url' in res_info['h264']:
                        src = res_info['h264']['url']
                        if not src.startswith('http'):
                            src = f"{base_url}{src}"
                        video_src = src
                        mimetype = "video/mp4"
                        break
        else:
             # Very basic cleanup if direct URL used
             pass


        if not video_src:
            # Show a placeholder if no URL is set
            return Fragment("<div>Please configure the MediaCMS Video URL in Studio.</div>")

        is_completed = self.progress >= self.completion_percentage
        html_context = {
            'display_name': self.display_name,
            'video_src': video_src,
            'mimetype': mimetype,
            'progress': self.progress,
            'completion_percentage': self.completion_percentage,
            'is_completed': is_completed,
            'is_completed_class': 'mediacms-completed' if is_completed else '',
            'progress_label': 'Done:' if is_completed else 'Progress:'
        }

        frag = Fragment(self.resource_string("static/html/mediacms.html").format(**html_context))
        
        
        # Add VideoJS Library (CDN)
        frag.add_css_url("https://vjs.zencdn.net/7.20.3/video-js.min.css")
        frag.add_javascript_url("https://vjs.zencdn.net/7.20.3/video.min.js")
        
        # Add JS and CSS
        frag.add_css(self.resource_string("static/css/mediacms.css"))
        frag.add_javascript(self.resource_string("static/js/src/mediacms.js"))
        frag.initialize_js('MediaCMSXBlock', {
            'completion_percentage': self.completion_percentage,
            'mediacms_url': self.mediacms_url,
            'last_watched_url': self.last_watched_url,
            'progress': self.progress,
            'watched_ranges': self.watched_ranges,
        })
        return frag

    def studio_view(self, context=None):
        """
        Editing view in Studio.
        """
        # Ensure we show the default URL even if the field is technically empty in DB (for old instances)
        url_to_show = self.mediacms_url
        if not url_to_show:
            url_to_show = "https://deic.mediacms.io/view?m=6ui2LMmEs"

        html_context = {
            'display_name': self.display_name,
            'mediacms_url': url_to_show,
            'completion_percentage': self.completion_percentage
        }
        
        frag = Fragment(self.resource_string("static/html/studio_edit.html").format(**html_context))
        frag.add_javascript(self.resource_string("static/js/src/studio_edit.js"))
        frag.initialize_js('MediaCMSStudioXBlock')
        return frag

    @XBlock.json_handler
    def studio_submit(self, data, suffix=''):
        """
        Called when submitting the studio edit form
        """
        self.display_name = data.get('display_name')
        self.mediacms_url = data.get('mediacms_url')
        
        # Safely handle completion percentage
        completion = data.get('completion_percentage')
        if not completion:
             self.completion_percentage = 90
        else:
            try:
                self.completion_percentage = int(completion)
            except ValueError:
                self.completion_percentage = 90
                
        return {'result': 'success'}

    @XBlock.json_handler
    def report_progress(self, data, suffix=''):
        """
        AJAX handler to update progress.
        Data keys: 'progress' (int).
        """
        try:
            client_progress = int(data.get('progress', 0))
        except ValueError:
            return {'result': 'error'}

        # Simple verification: don't allow regression unless resetting? 
        # Actually user might replay. But max progress counts.

        
        if client_progress > self.progress:
            self.progress = client_progress
        
        # Check completion
        # If progress >= threshold, we emit completion grade
        if self.progress >= self.completion_percentage:

            self.runtime.publish(self, 'grade', {
                'value': 1.0,
                'max_value': 1.0,
            })
            
        # Save ranges if provided
        ranges = data.get('watched_ranges')
        if ranges is not None:
            self.watched_ranges = ranges

        return {'progress': self.progress}

    @XBlock.json_handler
    def publish_completion(self, data, suffix=''):
        """
        Handler to accept completion publication from LMS.
        """

        return {'result': 'ok'}



    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("MediaCMSXBlock",
             """<mediacms/>
             """),
        ]
