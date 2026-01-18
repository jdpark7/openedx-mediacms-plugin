/* Javascript for MediaCMSXBlock. */
function MediaCMSXBlock(runtime, element, args) {

    args = args || {};


    var video = $(element).find('video')[0];
    if (!video) {
        return;
    }

    // Check if we are in Studio to prevent preview issues
    var isStudio = window.location.hostname.indexOf('studio') !== -1 || $(element).closest('.studio-xblock-wrapper').length > 0;
    if (isStudio) {

        return;
    }

    // We assume VideoJS is loaded globally or by the platform. 
    // If not, we might need a loader. For now, assume standard usage.
    // However, Open edX might not have videojs global. 
    // We'll fallback to native HTML5 if videojs is missing, but try to use it.

    var player = null;

    // Validate/Normalize viewedRanges (handle legacy [[0,10]] vs new [{start:0, end:10}])
    var rawRanges = args.watched_ranges || [];
    var viewedRanges = [];
    if (Array.isArray(rawRanges)) {
        viewedRanges = rawRanges.map(function (r) {
            if (Array.isArray(r) && r.length >= 2) return { start: r[0], end: r[1] };
            if (typeof r === 'object' && r.start !== undefined) return r;
            return null;
        }).filter(function (r) { return r; });
    }
    var lastUpdate = args.progress || 0;
    var cmid = 0; // Not used here, XBlock handles context
    var completionPercentage = args.completion_percentage || 90;

    var updateProgressUI = function (percent) {
        $(element).find('.progress-value').text(percent);
        if (percent >= completionPercentage) {
            $(element).find('.mediacms-progress-info').addClass('mediacms-completed');
            $(element).find('.progress-label').text('Done:');
        }
    };

    // Check for URL change and reset if needed
    // NOTE: This logic has been moved to the backend (mediacms.py) for reliability.
    // The server now resets progress before rendering if the URL has changed.

    var reportProgress = function (percent) {
        var handlerUrl = runtime.handlerUrl(element, 'report_progress');
        $.ajax({
            type: "POST",
            url: handlerUrl,
            data: JSON.stringify({
                progress: percent,
                watched_ranges: viewedRanges
            }),
            success: function (data) {

            },
            error: function (xhr, status, error) {
                console.error('MediaCMS: Progress save failed', error);
            }
        });
    };

    var onTimeUpdate = function () {
        var currentTime = player ? player.currentTime() : video.currentTime;
        var duration = player ? player.duration() : video.duration;

        if (duration > 0 && isFinite(duration)) {
            var rangeStart = Math.max(0, currentTime - 0.5);
            var rangeEnd = currentTime;

            // Merge logic (Same as Moodle)
            viewedRanges.push({ start: rangeStart, end: rangeEnd });
            viewedRanges.sort(function (a, b) { return a.start - b.start; });

            var consolidatedRanges = [];
            if (viewedRanges.length > 0) {
                var current = viewedRanges[0];
                for (var i = 1; i < viewedRanges.length; i++) {
                    if (viewedRanges[i].start <= current.end + 0.5) {
                        current.end = Math.max(current.end, viewedRanges[i].end);
                    } else {
                        consolidatedRanges.push(current);
                        current = viewedRanges[i];
                    }
                }
                consolidatedRanges.push(current);
            }
            viewedRanges = consolidatedRanges;

            var totalWatched = 0;
            viewedRanges.forEach(function (r) {
                totalWatched += (r.end - r.start);
            });

            var percentage = Math.floor((totalWatched / duration) * 100);
            if (percentage > 100) percentage = 100;

            updateProgressUI(percentage);

            // Report logic (throtte)
            if (percentage > lastUpdate && (percentage % 5 === 0 || percentage >= completionPercentage)) {
                lastUpdate = percentage;
                reportProgress(percentage);
            }
        }
    };

    var onEnded = function () {
        updateProgressUI(100);
        reportProgress(100);
    };

    // Initialize VideoJS if available
    if (typeof videojs !== 'undefined') {
        // Add specific class for VideoJS styling/hook *before* initialization
        $(video).addClass('video-js');

        player = videojs(video, {
            controls: true,
            autoplay: false,
            preload: 'auto',
            fluid: false, // Using CSS padding hack for sizing
            playbackRates: [0.5, 0.75, 1, 1.25, 1.5, 2]
        });
        player.on('timeupdate', onTimeUpdate);
        player.on('ended', onEnded);
    } else {
        // Native fallback
        // logger('Using native controls (VideoJS missing)'); // logger undefined, removing log or using console
        $(video).on('timeupdate', onTimeUpdate);
        $(video).on('ended', onEnded);
    }
}
