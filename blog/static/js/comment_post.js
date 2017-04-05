// Comment Form Scripts

$(function() {
  $("#commentForm input,#commentForm textarea").jqBootstrapValidation({
    preventSubmit: true,
    submitError: function($form, event, errors) {
      // additional error messages or events
    },
    submitSuccess: function($form, event) {
      event.preventDefault(); // prevent default submit behaviour
      // get values from FORM
      var name = $("input#name").val();
      var email = $("input#email").val();
      var message = $("textarea#message").val();
      var postSlug = $("#postSlug").val();
      var firstName = name; // For Success/Failure Message
      // Check for white space in name for Success/Fail message
      if (firstName.indexOf(' ') >= 0) {
        firstName = name.split(' ').slice(0, -1).join(' ');
      }
      $.ajax({
        url: "/comment",
        type: "POST",
        dataType: 'json',
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify({
          post_slug: postSlug,
          name: name,
          email: email,
          message: message
        }),
        cache: false,
        success: function() {
          // Success message
          $('#success').html("<div class='alert alert-success alert-dismissable fade show'>");
          $('#success > .alert-success').html("<button type='button' class='close' data-dismiss='alert' aria-hidden='true'>&times;")
            .append("</button>");
          $('#success > .alert-success')
            .append("Your comment has been sent.");
          $('#success > .alert-success')
            .append('</div>');

          //clear all fields
          $('#commentForm').trigger("reset");
        },
        error: function() {
          // Fail message
          $('#success').html("<div class='alert alert-danger alert-dismissable fade show'>");
          $('#success > .alert-danger').html("<button type='button' class='close' data-dismiss='alert' aria-hidden='true'>&times;")
            .append("</button>");
          $('#success > .alert-danger').append("Sorry " + firstName + ", it seems that something is wrong. Please try again later!");
          $('#success > .alert-danger').append('</div>');
          //clear all fields
          $('#commentForm').trigger("reset");
        },
      });
    },
    filter: function() {
      return $(this).is(":visible");
    },
  });

  $("a[data-toggle=\"tab\"]").click(function(e) {
    e.preventDefault();
    $(this).tab("show");
  });
});


/*When clicking on Full hide fail/success boxes */
$('#name').focus(function() {
  $('#success').html('');
});
