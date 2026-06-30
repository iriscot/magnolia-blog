"use strict";

function getCsrfToken() {
    const tokenInput = document.querySelector('input[name=csrfmiddlewaretoken]');
    return tokenInput ? tokenInput.value : '';
}

window.addEventListener("DOMContentLoaded", function() {
    const uploadAvatarButton = document.getElementById('upload_avatar');
    const fileUploadInput = document.getElementById('fileUpload');

    if (uploadAvatarButton && fileUploadInput) {
        uploadAvatarButton.addEventListener('click', function() {
            fileUploadInput.click();
        });
    }

    document.addEventListener('change', function(e) {
        if (e.target && e.target.id === 'fileUpload') {
            const selectedFile = e.target.files[0];
            if (!selectedFile) return;

            const formData = new FormData();
            formData.append('image', selectedFile);
            formData.append('csrfmiddlewaretoken', getCsrfToken());

            fetch('/api/images/header', {
                method: 'POST',
                body: formData
            })
            .then(function(response) {
                if (response.ok) {
                    return response.json();
                }
                throw new Error('Network response was not ok.');
            })
            .then(function(responseData) {
                document.getElementById('blog_avatar').src = responseData.url;
            })
            .catch(function(error) {
                alert(gettext('Something went wrong during upload'));
                console.error('[fetch]', error);
            });
        }
    });

    const searchBox = document.querySelector('.search-box');
    if (searchBox) {
        searchBox.addEventListener('click', function () {
            this.classList.add('active');
            this.querySelector('input').focus();
        });

        document.addEventListener('click', function (event) {
            if (!searchBox.contains(event.target) && searchBox.classList.contains('active')) {
                searchBox.classList.remove('active');
            }
        });
    }

    const searchForm = document.querySelector('#searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const searchInput = this.querySelector('input');
            const searchTerm = searchInput.value.trim();

            if (searchTerm.length > 0) {
                location.href = `/post/search/${encodeURIComponent(searchTerm)}/`;
            }
        });
    }

    document.querySelectorAll('.do_post_delete').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            const confirmDelete = confirm(gettext('Are you sure you want to delete this post?'));

            if (confirmDelete) {
                const postId = this.getAttribute('data-postid');
                const formData = new FormData();
                formData.append('id', postId);
                formData.append('csrfmiddlewaretoken', getCsrfToken());

                fetch('/api/posts/remove', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(() => {
                    if (location.pathname.match(/^\/post\//)) {
                        location.href = '/';
                    } else {
                        const blogPostToRemove = document.querySelector(`.blog-post[data-postid="${postId}"]`);
                        if (blogPostToRemove) {
                            blogPostToRemove.textContent = gettext('Post was removed.');
                        }
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                });
            }
        });
    });
});

function resolveEditorTool(label, candidates, required = false) {
    for (const candidate of candidates) {
        if (typeof window[candidate] === 'function') {
            return window[candidate];
        }
    }

    const message = `${label} tool is not loaded. Checked globals: ${candidates.join(', ')}`;

    if (required) {
        console.error(message);
    } else {
        console.warn(message);
    }

    return null;
}

function addTool(tools, name, toolClass, config = {}) {
    if (!toolClass) return;

    tools[name] = Object.keys(config).length > 0
        ? { class: toolClass, ...config }
        : toolClass;
}

function init_editor(saved_data = false) {
    const postTitleInput = document.getElementById("post-title");
    if (!postTitleInput) return;

    const initialPostData = saved_data || {};

    postTitleInput.addEventListener("input", function() {
        const inputValue = postTitleInput.value.trim();
        document.title = inputValue || gettext("New post");
    });

    const EditorClass = resolveEditorTool('EditorJS', ['EditorJS'], true);
    if (!EditorClass) {
        alert(gettext('Editor failed to load. Please rebuild static vendor files and refresh the page.'));
        return;
    }

    const HeaderTool = resolveEditorTool('Header', ['Header']);
    const ImageToolClass = resolveEditorTool('Image', ['ImageTool', 'Image']);
    const QuoteTool = resolveEditorTool('Quote', ['Quote']);
    const ListTool = resolveEditorTool('List', ['EditorjsList', 'EditorJSList', 'List', 'NestedList']);
    const EmbedTool = resolveEditorTool('Embed', ['Embed']);
    const RawToolClass = resolveEditorTool('Raw', ['RawTool', 'Raw']);
    const ChecklistTool = resolveEditorTool('Checklist', ['Checklist', 'CheckList']);
    const DelimiterTool = resolveEditorTool('Delimiter', ['Delimiter']);

    const tools = {};

    addTool(tools, 'header', HeaderTool, {
        config: {
            levels: [2],
            defaultLevel: 2
        }
    });

    addTool(tools, 'image', ImageToolClass, {
        config: {
            additionalRequestData: {
                csrfmiddlewaretoken: getCsrfToken(),
            },
            endpoints: {
                byFile: '/api/images/file',
                byUrl: '/api/images/link',
            },
            uploader: {
                uploadByUrl: (url) => {
                    const body = new URLSearchParams({
                        csrfmiddlewaretoken: getCsrfToken(),
                        url: url,
                    });
                    return fetch('/api/images/link', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: body.toString(),
                    }).then(response => response.json());
                }
            },
        }
    });

    addTool(tools, 'quote', QuoteTool, { inlineToolbar: true });

    if (ListTool) {
        addTool(tools, 'list', ListTool, {
            inlineToolbar: true,
            config: {
                defaultStyle: 'unordered'
            }
        });
    }

    addTool(tools, 'embed', EmbedTool, {
        config: {
            services: {
                youtube: true,
            }
        }
    });

    addTool(tools, 'raw', RawToolClass);

    if (ChecklistTool) {
        addTool(tools, 'checklist', ChecklistTool, { inlineToolbar: true });
    } else if (ListTool) {
        // @editorjs/checklist is deprecated; @editorjs/list 2.x can create checklist-style blocks.
        addTool(tools, 'checklist', ListTool, {
            inlineToolbar: true,
            config: {
                defaultStyle: 'checklist'
            }
        });
    }

    addTool(tools, 'delimiter', DelimiterTool);

    const editor = new EditorClass({
        holder: 'post-editor',
        placeholder: gettext('Here goes your new article...'),
        tools: tools,
        autofocus: true,
        data: initialPostData.content || undefined,
    });

    document.addEventListener('click', function(e) {
        if (e.target && e.target.id === 'savePreviewNote') {
            e.preventDefault();
            editor.save().then(function(outputData) {
                if (outputData.blocks.length === 0) return;
                const formData = new FormData();
                formData.append('title', document.getElementById('post-title').value);
                formData.append('content', JSON.stringify(outputData));
                formData.append('tags', document.getElementById('post-tags').value);
                formData.append('csrfmiddlewaretoken', getCsrfToken());
                formData.append('id', initialPostData.id || '');

                fetch('/api/posts/edit', {
                    method: 'POST',
                    body: formData
                })
                .then(function(response) {
                    if (response.ok) {
                        return response.json();
                    }
                    throw new Error('Network response was not ok.');
                })
                .then(function(data) {
                    window.location = data.url;
                })
                .catch(function(error) {
                    console.error('[fetch]', error);
                });
            });
        }
    });
}
