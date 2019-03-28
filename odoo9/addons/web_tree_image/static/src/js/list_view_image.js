//openerp_Branding = function(instance) {
odoo.define('web_tree_image.ListView', function (require) {
"use strict";

var core = require('web.core');
//var _t = core._t;
var session = require('web.session');
var QWeb = core.qweb;
var list_widget_registry = core.list_widget_registry;
//console.log('list_widget_registry::', list_widget_registry);
var WebListView = require('web.ListView');
//Evar list_widget_registry = WebListView.list_widget_registry;

//console.log('aweWebListView.Column=',WebListView.MetaColumn);
//console.log(WebListView.List, '@');
//WebListView.include({
//WebListView.ColumnImage = WebListView.Column.extend({
var Column = list_widget_registry.get('field');
var	ColumnImage = Column.extend({
	//var	ColumnImage = WebListView.MetaColumn.extend({	
	
	    /**
	     * Return a link to the binary data as a file
	     *
	     * @private
	     */
	    _format: function (row_data, options) {
	    	//console.log('COL-IMAGE._FORMAT CALLED');
	        //var text = _t("Download"), filename=_t('Binary file');
	        var value = row_data[this.id].value; 
	        var	src;
	        if (!value) {
	            return options.value_if_empty || '';
	        }

	        if (this.type === 'binary') {
                if (value && value.substr(0, 10).indexOf(' ') === -1) {
                    // The media subtype (png) seems to be arbitrary
                    src = "data:image/png;base64," + value;
                } else {
                    var imageArgs = {
                        model: options.model,
                        field: this.id,
                        id: options.id
                    }
                    if (this.resize) {
                        imageArgs.resize = this.resize;
                    }
                    src = session.url('/web/binary/image', imageArgs);
                }
            } else {
                if (!/\//.test(row_data[this.id].value)) {
                    src = '/web/static/src/img/icons/' + row_data[this.id].value + '.png';
                } else {
                    src = row_data[this.id].value;
                }
            }
	        //---------------
	        /*var download_url;
	        if (value.substr(0, 10).indexOf(' ') == -1) {
	            download_url = "data:application/octet-stream;base64," + value;
	        } else {
	            download_url = session.url('/web/content', {model: options.model, field: this.id, id: options.id, download: true});
	            if (this.filename) {
	                download_url += '&filename_field=' + this.filename;
	            }
	        }
	        if (this.filename && row_data[this.filename]) {
	            text = _.str.sprintf(_t("Download \"%s\""), formats.format_value(
	                    row_data[this.filename].value, {type: 'char'}));
	            filename = row_data[this.filename].value;
	        }*/
	        var template = 'ListView.row.image';
	        return QWeb.render(template, {
	            widget: this,
	            src: src /*,
	            prefix: session.prefix,
	            disabled: attrs.readonly
	                || isNaN(row_data.id.value)
	                || data.BufferedDataSet.virtual_id_regex.test(row_data.id.value)
	                */
	        });

	        /*return _.template('<a download="<%-download%>" href="<%-href%>"><%-text%></a> (<%-size%>)')({
	            text: text,
	            href: download_url,
	            size: utils.binary_to_binsize(value),
	            download: filename,
	        });*/
	    }
	});
		//});
	
	list_widget_registry
	.add('field.image', ColumnImage);
	
	//console.log('list_widget_registry2', list_widget_registry);
	/*WebListView.include({
	    init: function(parent, client_options) {
	        this._super(parent);
	        this.set('title_part', {"zopenerp": "AADC"});
	    }
	    //ColumnImage = ColumnImage
	});*/
	

});
