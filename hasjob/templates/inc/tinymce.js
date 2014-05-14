{%- if config['TYPEKIT_CODE'] %}
// From https://gist.github.com/Zae/3742398
(function() {
  tinymce.create('tinymce.plugins.typekit', {
    init: function(ed, url) {
      ed.onPreInit.add(function(ed) {

        // Get the DOM document object for the IFRAME
        var doc = ed.getDoc();

        // Create the script we will add to the header asynchronously
        var jscript = "(function() {\n\
          var config = {\n\
            kitId: '{{ config['TYPEKIT_CODE']|e }}'\n\
          };\n\
          var d = false;\n\
          var tk = document.createElement('script');\n\
          tk.src = '//use.typekit.com/' + config.kitId + '.js';\n\
          tk.type = 'text/javascript';\n\
          tk.async = 'true';\n\
          tk.onload = tk.onreadystatechange = function() {\n\
            var rs = this.readyState;\n\
            if (d || rs && rs != 'complete' && rs != 'loaded') return;\n\
            d = true;\n\
            try { Typekit.load(config); } catch (e) {}\n\
          };\n\
          var s = document.getElementsByTagName('script')[0];\n\
          s.parentNode.insertBefore(tk, s);\n\
        })();";

        // Create a script element and insert the TypeKit code into it
        var script = doc.createElement("script");
        script.type = "text/javascript";
        script.text = jscript;

        // Add the script to the header
        doc.getElementsByTagName('head')[0].appendChild(script);

      });

    },
    getInfo: function() {
      return {
        longname: 'TypeKit For TinyMCE',
        author: 'Tom J Nowell',
        authorurl: 'http://tomjn.com/',
        infourl: 'http://twitter.com/tarendai',
        version: "1.1"
      };
    }
  });
  tinymce.PluginManager.add('typekit', tinymce.plugins.typekit);
})();
{%- endif %}

$(function() {
  tinymce.init({
    selector: 'textarea.tinymce',

    // General options
    {% if config['TYPEKIT_CODE'] -%}
      plugins : "typekit",
    {%- endif %}

    // Options (TinyMCE 4)
    plugins: "autolink autoresize link lists paste searchreplace",
    toolbar: "bold italic | bullist numlist | link unlink | searchreplace undo redo",
    statusbar: false,
    menubar: false,
    resize: true,

    valid_elements: "p,br,strong/b,em/i,ul,ol,li,a[!href|title|target]",
    width: "100%",
    height: "400",
    // Content CSS
    content_css: {% assets filters="cssmin", output="css/editor.packed.css", "css/editor.css" %}{{ ASSET_URL|tojson }}{% endassets %},
    setup: function(ed) {
      // This doesn't work well yet
      // ed.on('init', function(e) {
      //   $(ed.editorContainer).find('.mce-toolbar-grp').each(function() {
      //     var edc = $(ed.editorContainer), toolbar = $(this);
      //     toolbar.affix({
      //       offset: {
      //         top: function() {return toolbar.offset().top},
      //         bottom: function() {return edc.offset().top + edc.outerHeight(true)}
      //       }
      //     })
      //   });
      // });
      ed.on('focus', function(e) {
        $(ed.editorContainer).addClass('active');
      });
      ed.on('blur', function(e) {
        $(ed.editorContainer).removeClass('active');
      });
    } // End of setup keyval
  });
});
