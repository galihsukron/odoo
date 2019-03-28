odoo.define('web.BoxView', function (require) {
"use strict";
/*---------------------------------------------------------
 * My Box view
 *---------------------------------------------------------*/

var core = require('web.core');
var data = require('web.data');
var formats = require('web.formats');
var pyeval = require('web.pyeval');
var session = require('web.session');
var utils = require('web.utils');
var View = require('web.View');

//var KanbanRecord = require('web_kanban.Record');

var _lt = core._lt;
var QWeb = core.qweb;

var BoxView = View.extend(/** @lends instance.web.BoxView# */{
	className: "o_box_view",
    display_name: _lt('Box'),
    template: "BoxView",
    icon: 'fa-film',
    view_type: 'box',
    /**
     * Indicates that this view is not searchable, and thus that no search
     * view should be displayed (if there is one active).
     */
    //searchable : false,
    /**
     * Genuine box view (the one displayed as a box, not the list)
     *
     * @constructs instance.web.BoxView
     * @extends instance.web.View
     *
     * @param parent
     * @param dataset
     * @param view_id
     * @param options
     */
    init: function(parent, dataset, view_id, options) {
        this._super(parent, dataset, view_id, options);
        this.dataset = dataset;
        this.model = dataset.model;
        this.view_id = view_id;

        this.records = {};
        this.fields_view = [];

        this.options = _.extend({}, this.defaults, options || {});
        this.search_orderer = new utils.DropMisordered();
        //_.bindAll(this, 'color_for');
    },

    view_loading: function(fvg) {
        this.$el.addClass(fvg.arch.attrs.class);
        this.fields_view = fvg;
        this.default_group_by = fvg.arch.attrs.default_group_by;

        this.fields_keys = _.keys(this.fields_view.fields);

        // use default order if defined in xml description
        var default_order = this.fields_view.arch.attrs.default_order;
        if (!this.dataset._sort.length && default_order) {
            this.dataset.set_sort(default_order.split(','));
        }
        // add qweb templates
    	
        return this.load_box(fvg);
    },

    /**
     * Returns the list of fields needed to correctly read objects.
     *
     * Gathers the names of all fields in fields_view_get, and adds the
     * field_parent (children_field in the box view) if it's not already one
     * of the fields to fetch
     *
     * @returns {Array} an array of fields which can be provided to DataSet.read_slice and others
     */
    fields_list: function () {
        var fields = _.keys(this.fields);
        if (!_(fields).contains(this.children_field)) {
            fields.push(this.children_field);
        }
        return fields;
    },
    load_box: function (fields_view) {
    	console.log('LLOaDBOX', fields_view)
        var self = this;
        var has_toolbar = !!fields_view.arch.attrs.toolbar;
        // field name in OpenERP is kinda stupid: this is the name of the field
        // holding the ids to the children of the current node, why call it
        // field_parent?
        //this.children_field = fields_view.field_parent;
        this.fields_view = fields_view;
        _(this.fields_view.arch.children).each(function (field) {
            if (field.attrs.modifiers) {
                field.attrs.modifiers = JSON.parse(field.attrs.modifiers);
            }
        });
        this.fields = fields_view.fields;
        this.hook_row_click();
        this.$el.html(QWeb.render('BoxView', {
            'title': this.fields_view.arch.attrs.string,
            'fields_view': this.fields_view.arch.children,
            'fields': this.fields,
            'toolbar': has_toolbar
        }));
        this.$el.addClass(this.fields_view.arch.attrs['class']);

        this.dataset.read_slice(this.fields_list()).done(function(records) {
            if (!has_toolbar) {
                // WARNING: will do a second read on the same ids, but only on
                //          first load so not very important
                self.getdata(null, _(records).pluck('id'));
                return;
            }

            var $select = self.$el.find('select')
                .change(function () {
                    var $option = $(this).find(':selected');
                    self.getdata($option.val(), $option.data('children'));
                });
            _(records).each(function (record) {
                self.records[record.id] = record;
                $('<option>')
                        .val(record.id)
                        .text(record.name)
                        .data('children', record[self.children_field])
                    .appendTo($select);
            });

            if (!_.isEmpty(records)) {
                $select.change();
            }
        });

        // TODO store open nodes in url ?...
        this.do_push_state({});

        if (!this.fields_view.arch.attrs.colors) {
            return;
        }
        this.colors = _(this.fields_view.arch.attrs.colors.split(';')).chain()
            .compact()
            .map(function(color_pair) {
                var pair = color_pair.split(':'),
                    color = pair[0],
                    expr = pair[1];
                return [color, py.parse(py.tokenize(expr)), expr];
            }).value();
    },
    do_search: function(domain, context, group_by) {
        var self = this;
        var group_by_field = group_by[0] || this.default_group_by;
        var field = this.fields_view.fields[group_by_field];
        var grouped_by_m2o = field && (field.type === 'many2one');

        var options = {
            search_domain: domain,
            search_context: context,
            group_by_field: group_by_field,
            grouped: group_by.length || this.default_group_by,
            grouped_by_m2o: grouped_by_m2o,
            relation: (grouped_by_m2o ? field.relation : undefined),
        };

        return this.search_orderer
            .add(options.grouped ? this.load_groups(options) : this.load_records())
            .then(function (data) {
                _.extend(self, options);
                if (options.grouped) {
                    var new_ids = _.union.apply(null, _.map(data.groups, function (group) {
                        return group.dataset.ids;
                    }));
                    self.dataset.alter_ids(new_ids);
                }
                self.data = data;
            })
            //.then(this.proxy('render'))
            //.then(this.proxy('update_pager'));
            ;
    },
    render: function () {
        // cleanup
        this.$el.css({display:'-webkit-flex'});
        this.$el.css({display:'flex'});
        this.$el.removeClass('o_kanban_ungrouped o_kanban_grouped');
        _.invoke(this.widgets, 'destroy');
        this.$el.empty();
        this.widgets = [];
        if (this.column_quick_create) {
            this.column_quick_create.destroy();
            this.column_quick_create = undefined;
        }

        this.record_options = {
            editable: this.is_action_enabled('edit'),
            deletable: this.is_action_enabled('delete'),
            fields: this.fields_view.fields,
            qweb: this.qweb,
            model: this.model,
            read_only_mode: this.options.read_only_mode,
        };

        // actual rendering
        var fragment = document.createDocumentFragment();
        if (this.data.grouped) {
            this.$el.addClass('o_kanban_grouped');
            this.render_grouped(fragment);
        } else if (this.data.is_empty) {
            this.$el.addClass('o_kanban_ungrouped');
            this.render_no_content(fragment);
        } else {
            this.$el.addClass('o_kanban_ungrouped');
            this.render_ungrouped(fragment);
        }
        this.$el.append(fragment);
    },

    render_no_content: function (fragment) {
        var content = QWeb.render('KanbanView.nocontent', {content: this.no_content_msg});
        $(content).appendTo(fragment);
    },

    render_ungrouped: function (fragment) {
        var self = this;
        var options = _.clone(this.record_options);
        _.each(this.data.records, function (record) {
            var kanban_record = new KanbanRecord(self, record, options);
            self.widgets.push(kanban_record);
            kanban_record.appendTo(fragment);
        });

        // add empty invisible divs to make sure that all kanban records are left aligned
        for (var i = 0, ghost_div; i < 6; i++) {
            ghost_div = $("<div>").addClass("o_kanban_record o_kanban_ghost");
            ghost_div.appendTo(fragment);
        }
        this.postprocess_m2m_tags();
    },
    do_show: function() {
        this.do_push_state({});
        return this._super();
    },

    do_reload: function() {
        this.do_search(this.search_domain, this.search_context, [this.group_by_field]);
    },

    load_records: function (offset, dataset) {
        var options = {
            'limit': this.limit,
            'offset': offset,
        };
        dataset = dataset || this.dataset;
        return dataset
            .read_slice(this.fields_keys.concat(['__last_update']), options)
            .then(function(records) {
                return {
                    records: records,
                    is_empty: !records.length,
                    grouped: false,
                };
            });
    },

    load_groups: function (options) {
        var self = this;
        var group_by_field = options.group_by_field;
        var fields_keys = _.uniq(this.fields_keys.concat(group_by_field));

        return new Model(this.model, options.search_context, options.search_domain)
        .query(fields_keys)
        .group_by([group_by_field])
        .then(function (groups) {

            // Check in the arch the fields to fetch on the stage to get tooltips data.
            // Fetching data is done in batch for all stages, to avoid doing multiple
            // calls. The first naive implementation of group_by_tooltip made a call
            // for each displayed stage and was quite limited.
            // Data for the group tooltip (group_by_tooltip) and to display stage-related
            // legends for kanban state management (states_legend) are fetched in
            // one call.
            var group_by_fields_to_read = [];
            var group_options = {};
            var recurse = function(node) {
                if (node.tag === "field" && node.attrs && node.attrs.options && node.attrs.name === group_by_field) {
                    var options = pyeval.py_eval(node.attrs.options);
                    group_options = options;
                    var states_fields_to_read = _.map(
                        options && options.states_legend || {},
                        function (value, key, list) { return value; });
                    var tooltip_fields_to_read = _.map(
                        options && options.group_by_tooltip || {},
                        function (value, key, list) { return key; });
                    group_by_fields_to_read = _.union(
                        group_by_fields_to_read,
                        states_fields_to_read,
                        tooltip_fields_to_read);
                    return;
                }
                _.each(node.children, function(child) {
                    recurse(child);
                });
            };
            recurse(self.fields_view.arch);

            // fetch group data (display information)
            var group_ids = _.without(_.map(groups, function (elem) { return elem.attributes.value[0];}), undefined);
            if (options.grouped_by_m2o && group_ids.length) {
                return new data.DataSet(self, options.relation)
                    .read_ids(group_ids, _.union(['display_name'], group_by_fields_to_read))
                    .then(function(results) {
                        _.each(groups, function (group) {
                            var group_id = group.attributes.value[0];
                            var result = _.find(results, function (data) {return group_id === data.id;});
                            group.title = result ? result.display_name : _t("Undefined");
                            group.values = result;
                            group.id = group_id;
                            group.options = group_options;
                        });
                        return groups;
                    });
            } else {
                _.each(groups, function (group) {
                    var value = group.attributes.value;
                    group.id = value instanceof Array ? value[0] : value;
                    var field = self.fields_view.fields[options.group_by_field];
                    if (field && field.type === "selection") {
                        value= _.find(field.selection, function (s) { return s[0] === group.id; });
                    }
                    group.title = (value instanceof Array ? value[1] : value) || _t("Undefined");
                    group.values = {};
                });
                return $.when(groups);
            }
        })
        .then(function (groups) {
            var undef_index = _.findIndex(groups, function (g) { return g.title === _t("Undefined");});
            if (undef_index >= 1) {
                var undef_group = groups[undef_index];
                groups.splice(undef_index, 1);
                groups.unshift(undef_group);
            }
            return groups;
        })
        .then(function (groups) {
            // load records for each group
            var is_empty = true;
            return $.when.apply(null, _.map(groups, function (group) {
                var def = $.when([]);
                var dataset = new data.DataSetSearch(self, self.dataset.model,
                    new data.CompoundContext(self.dataset.get_context(), group.model.context()), group.model.domain());
                if (self.dataset._sort) {
                    dataset.set_sort(self.dataset._sort);
                }
                if (group.attributes.length >= 1) {
                    def = dataset.read_slice(self.fields_keys.concat(['__last_update']), { 'limit': self.limit });
                }
                return def.then(function (records) {
                    self.dataset.ids.push.apply(self.dataset.ids, _.difference(dataset.ids, self.dataset.ids));
                    group.records = records;
                    group.dataset = dataset;
                    is_empty = is_empty && !records.length;
                    return group;
                });
            })).then(function () {
                return {
                    groups: Array.prototype.slice.call(arguments, 0),
                    is_empty: is_empty,
                    grouped: true,
                };
            });
        });
    },

    /**
     * Returns the color for the provided record in the current view (from the
     * ``@colors`` attribute)
     *
     * @param {Object} record record for the current row
     * @returns {String} CSS color declaration
     */
    color_for: function (record) {
        if (!this.colors) { return ''; }
        var context = _.extend({}, record, {
            uid: session.uid,
            current_date: moment().format('YYYY-MM-DD')
            // TODO: time, datetime, relativedelta
        });
        for(var i=0, len=this.colors.length; i<len; ++i) {
            var pair = this.colors[i],
                color = pair[0],
                expression = pair[1];
            if (py.PY_isTrue(py.evaluate(expression, context))) {
                return 'color: ' + color + ';';
            }
            // TODO: handle evaluation errors
        }
        return '';
    },
    /**
     * Sets up opening a row
     */
    hook_row_click: function () {
        var self = this;
        this.$el.delegate('.boxview-td span, .boxview-tr span', 'click', function (e) {
            e.stopImmediatePropagation();
            self.activate($(this).closest('tr').data('id'));
        });

        this.$el.delegate('.boxview-tr', 'click', function () {
            var is_loaded = 0,
                $this = $(this),
                record_id = $this.data('id'),
                row_parent_id = $this.data('row-parent-id'),
                record = self.records[record_id],
                children_ids = record[self.children_field];

            _(children_ids).each(function(childid) {
                if (self.$el.find('[id=boxrow_' + childid + '][data-row-parent-id='+ record_id +']').length ) {
                    if (self.$el.find('[id=boxrow_' + childid + '][data-row-parent-id='+ record_id +']').is(':hidden')) {
                        is_loaded = -1;
                    } else {
                        is_loaded++;
                    }
                }
            });
            if (is_loaded === 0) {
                if (!$this.parent().hasClass('oe_open')) {
                    self.getdata(record_id, children_ids);
                }
            } else {
                self.showcontent($this, record_id, is_loaded < 0);
            }
        });
    },
    // get child data of selected value
    getdata: function (id, children_ids) {
        var self = this;

        self.dataset.read_ids(children_ids, this.fields_list()).done(function(records) {
            _(records).each(function (record) {
                self.records[record.id] = record;
            });
            var $curr_node = self.$el.find('#boxrow_' + id);
            var children_rows = QWeb.render('BoxView.rows', {
                'records': records,
                'children_field': self.children_field,
                'fields_view': self.fields_view.arch.children,
                'fields': self.fields,
                'level': $curr_node.data('level') || 0,
                'render': formats.format_value,
                'color_for': self.color_for,
                'row_parent_id': id
            });
            if ($curr_node.length) {
                $curr_node.addClass('oe_open');
                $curr_node.after(children_rows);
            } else {
                self.$el.find('tbody').html(children_rows);
            }
        });
    },

    // Get details in listview
    activate: function(id) {
        var self = this;
        var local_context = {
            active_model: self.dataset.model,
            active_id: id,
            active_ids: [id]
        };
        var ctx = pyeval.eval(
            'context', new data.CompoundContext(
                this.dataset.get_context(), local_context));
        return this.rpc('/web/boxview/action', {
            id: id,
            model: this.dataset.model,
            context: ctx
        }).then(function (actions) {
            if (!actions.length) { return; }
            var action = actions[0][2];
            var c = new data.CompoundContext(local_context).set_eval_context(ctx);
            if (action.context) {
                c.add(action.context);
            }
            action.context = c;
            return self.do_action(action);
        });
    },

    // show & hide the contents
    showcontent: function (curnode,record_id, show) {
        curnode.parent('tr').toggleClass('oe_open', show);
        _(this.records[record_id][this.children_field]).each(function (child_id) {
            var $child_row = this.$el.find('[id=boxrow_' + child_id + '][data-row-parent-id='+ curnode.data('id') +']');
            if ($child_row.hasClass('oe_open')) {
                $child_row.toggleClass('oe_open',show);
                this.showcontent($child_row, child_id, false);
            }
            $child_row.toggle(show);
        }, this);
    },

    do_hide: function () {
        this.hidden = true;
        this._super();
    }
});

core.view_registry.add('box', BoxView);

return BoxView;

});

