function MediaCMSStudioXBlock(runtime, element) {
    $(element).find('.save-button').unbind('click').bind('click', function () {
        console.log('MediaCMS: Save button clicked');
        var handlerUrl = runtime.handlerUrl(element, 'studio_submit');

        // Visual feedback
        var $btn = $(this);
        $btn.text('Saving...').addClass('is-disabled');

        var data = {
            display_name: $(element).find('input[name=display_name]').val(),
            mediacms_url: $(element).find('input[name=mediacms_url]').val(),
            completion_percentage: $(element).find('input[name=completion_percentage]').val()
        };

        // Standard jQuery POST
        $.ajax({
            type: "POST",
            url: handlerUrl,
            data: JSON.stringify(data),
            success: function (response) {
                console.log('MediaCMS: Save successful. Notifying Studio...');
                // Success! Use standard notify to refresh the block
                runtime.notify('save', { state: 'end' });
            },
            error: function () {
                // Error handling fallback
                $btn.text('Save').removeClass('is-disabled');
                alert("Error saving. Please check the logs.");
            }
        });
    });

    $(element).find('.cancel-button').bind('click', function () {
        // Just reload for cancel too if notify is broken, but cancel usually works
        runtime.notify('cancel', {});
    });
}
