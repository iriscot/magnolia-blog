"use strict";

window.addEventListener("DOMContentLoaded", function() {


    $(document).on('click', '.update-header-images', (e) => {
        window.uploadImageType = $(e.currentTarget).data('type');
        $('#fileUpload').click();
    });

    $(document).on('change', '#fileUpload', (e) => {
        var formData = new FormData();
        formData.append('image', $('#fileUpload')[0].files[0]);
        formData.append('csrfmiddlewaretoken', $('input[name=csrfmiddlewaretoken]').val());
        formData.append('image_type', window.uploadImageType);

        $.ajax({
            url: '/api/images/header',
            type: "POST",
            processData: false,
            contentType: false,
            cache: false,
            enctype: 'multipart/form-data',
            data: formData,
            success: function(data) {
                location.reload();
            },
            error: function(data) {
                alert(gettext('Something went wrong during upload'));
            }
        });
    });




    $(document).on('click', '.search-box', (e) => {
        $(e.currentTarget).addClass('active').find('input').focus();
    });

    document.addEventListener('click', (event) => {
        var $target = $(event.target);
        if (!$target.closest('.search-box').length && $('.search-box').hasClass('active')) {
            $('.search-box').removeClass('active');
        }
    });

    $(document).on('submit', '#searchForm', (e) => {
        e.preventDefault()
        var search_term = $(e.currentTarget).find('input').val();
        if (search_term.length > 0)
            location.href = `/posts/search/${search_term}/`;
    })


});

function init_editor(saved_data = false) {
    var editor = new EditorJS({
        holder: 'post-editor',
        placeholder: gettext('Here goes your new article...'),
        tools: {
            header: {
                class: Header,
                config: {
                    levels: [2],
                    defaultLevel: 2
                }
            },
            image: {
                class: ImageTool,
                config: {
                    additionalRequestData: {
                        csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
                    },
                    endpoints: {
                        byFile: '/api/images/file',
                        byUrl: '/api/images/link',
                    },
                    uploader: {
                        uploadByUrl: (url) => {
                            return new Promise((resolve, reject) => {
                                $.ajax({
                                    url: '/api/images/link',
                                    data: {
                                        csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
                                        url: url,
                                    },
                                    method: 'POST',
                                    dataType: 'json',
                                    success: (data) => resolve(data),
                                    error: (data) => reject(data),
                                });
                            })
                        }
                    },
                }
            },
            quote: Quote,
            list: List,
            embed: {
                class: Embed,
                config: {
                    services: {
                        youtube: true,
                    }
                }
            },
            raw: RawTool,
            checklist: Checklist,
            delimiter: Delimiter,
        },
        autofocus: true,
        data: saved_data.content || undefined,
    });


    $(document).on('click', '#savePreviewNote', (e) => {
        e.preventDefault();
        editor.save().then((outputData) => {
            if (outputData.blocks.length === 0) return;
            $.ajax({
                type: 'POST',
                url: '/api/posts/edit',
                dataType: 'json',
                data: {
                    title: $('#post-title').val(),
                    content: JSON.stringify(outputData),
                    tags: $('#post-tags').val(),
                    csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
                    id: saved_data.id || undefined,
                },
                success: function(data) {
                    window.location = data.url;
                },
                error: function(xhr, errmsg, err) {
                    console.log(xhr.status + ": " + xhr.responseText);
                }
            });
        });
    });
}