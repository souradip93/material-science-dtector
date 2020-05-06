/*
 * jQuery File Upload Demo
 * https://github.com/blueimp/jQuery-File-Upload
 *
 * Copyright 2010, Sebastian Tschan
 * https://blueimp.net
 *
 * Licensed under the MIT license:
 * https://opensource.org/licenses/MIT
 */

/* global $ */

$(function () {
  'use strict';

  // Initialize the jQuery File Upload widget:
  $('#fileupload').fileupload({
    // Uncomment the following to send cross-domain cookies:
    xhrFields: {withCredentials: true},
    autoUpload:true,
    maxNumberOfFiles: 10,
    acceptFileTypes: /(\.|\/)(pdf)$/i,
    progressall : function (e, data) {
        var progress = parseInt(data.loaded / data.total * 100, 10);
        progress = ~~progress;
        $(".progress-bar-global").width(progress + '%');
        $(".progress-bar-global").html(progress+'%');
    },
    stop : function (e){
      $("#process").prop('disabled', false);
    },
    start : function (e){
      $("#process").prop('disabled', true);
    }
    // url: "{% url 'upload2' %}"
  });


  $('#fileupload').addClass('fileupload-processing');
  $.ajax({
    // Uncomment the following to send cross-domain cookies:
    //xhrFields: {withCredentials: true},
    url: $('#fileupload').fileupload('option', 'url'),
    dataType: 'json',
    context: $('#fileupload')[0]
  })
    .always(function () {
      $(this).removeClass('fileupload-processing');
    })
    .done(function (result) {
      $(this)
        .fileupload('option', 'done')
        // eslint-disable-next-line new-cap
        .call(this, $.Event('done'), { result: result });
    });
});
