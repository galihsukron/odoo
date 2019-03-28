odoo.define('web.CircleView', function (require) {
"use strict";
/*---------------------------------------------------------
 * My Circle view
 *---------------------------------------------------------*/

var core = require('web.core');
var data = require('web.data');
var Model = require('web.DataModel');
var formats = require('web.formats');
var pyeval = require('web.pyeval');
var session = require('web.session');
var utils = require('web.utils');
var View = require('web.View');

//var KanbanRecord = require('web_kanban.Record');

var _lt = core._lt;
var _t = core._t;
var QWeb = core.qweb;

var CircleView = View.extend(/** @lends instance.web.CircleView# */{
	className: "o_circle_view",
    display_name: _lt('Circle'),
    template: "CircleView",
    icon: 'fa-share-alt',
    view_type: 'circle',
    /**
     * Indicates that this view is not searchable, and thus that no search
     * view should be displayed (if there is one active).
     */
    //searchable : false,
    /**
     * Genuine circle view (the one displayed as a circle, not the list)
     *
     * @constructs instance.web.CircleView
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
    	
        return this.load_circle(fvg);
    },

    /**
     * Returns the list of fields needed to correctly read objects.
     *
     * Gathers the names of all fields in fields_view_get, and adds the
     * field_parent (children_field in the circle view) if it's not already one
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
    load_circle: function (fields_view) {
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
        this.$el.html(QWeb.render('CircleView', {
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
            .then(this.proxy('resolve_dependencies'))
            .then(this.proxy('render'))
            //.then(this.proxy('update_pager'));
            ;
    },
    resolve_dependencies : function () {
    	var depends = [];
    	var self = this;
    	self.child_cnx = {};
    	_.each(this.data.records, function (record) {
        	//id2index.push(record.id);
        	//names.push(record.name);
        	if (record.dependencies_id.length) 
        		depends = depends.concat(record.dependencies_id);
        });
        
        // remap
        
        if (depends.length) {
        	/*this.ds_depends = new data.DataSetSearch(this, );// 'ir.attachment');
            this.ds_depends.call('read', [depends, ['name','id']]).then(function (datas) {
                _.each(datas, function (data) {
                	console.log('tHE datAS', data);
                	child_cnx[data.id] = data.name;
                });                
            });*/
            return new Model(this.fields_view.fields.dependencies_id.relation).call("read", [depends, ['name','id']]).done(function(datas) {
            	_.each(datas, function (data) {
                	console.log('tHE datAS', data);
                	self.child_cnx[data.id] = data.name;
                });                
            });
        }
        this.depends = depends;
    },
    render: function () {
    	var self = this;
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
        
        // prepare d3js
        var width = 960,
        height = 500;

	    var color = d3.scale.category20();
	
	    this.d3force = d3.layout.force()
	        .charge(-20)
	        .linkDistance(30)
	        .size([width, height]);
	
	    //this.svg = d3.select(this.$el).append("svg")
	    this.svg = d3.select('body').append("svg")
	        .attr("width", width)
	        .attr("height", height);
	    //------------------------------------
	    
	    

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
        var text;
        var options = _.clone(this.record_options);
        var nodes = [];
        var id2index = [];
        var names =[];
        var depends =[];
        
        // define arrow markers for graph links
        this.svg.append('svg:defs').append('svg:marker')
            .attr('id', 'end-arrow')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 6)
            .attr('markerWidth', 3)
            .attr('markerHeight', 3)
            .attr('orient', 'auto')
          .append('svg:path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', '#000');

        this.svg.append('svg:defs').append('svg:marker')
            .attr('id', 'start-arrow')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 4)
            .attr('markerWidth', 3)
            .attr('markerHeight', 3)
            .attr('orient', 'auto')
          .append('svg:path')
            .attr('d', 'M10,-5L0,0L10,5')
            .attr('fill', '#000');
        // nodes:
        //var idx = 0;
        _.each(this.data.records, function (record) {
        	id2index.push(record.id);
        	names.push(record.name);
        	if (record.dependencies_id.length) 
        		depends = depends.concat(record.dependencies_id);
            /*  var kanban_record = new KanbanRecord(self, record, options);
            self.widgets.push(kanban_record);
            kanban_record.appendTo(fragment);
            */
        	var rec = {'name': record['name'], 'group': 0, 'app' : record.application};
        	if (record.category_id.length)
        		rec['group'] = record.category_id[0];
        	
        	nodes.push(rec);
        	console.log("rendEr-ungroup.record=", record);
        	//var kanban_record = $("<div/>").text("Text.");   // Create with jQuery
        	//kanban_record.appendTo(fragment);
        });
        console.log('nODEs', nodes);
        console.log('id2IndeX', id2index);
        console.log(names);
        
        // remap
        var child_cnx = this.child_cnx;
        /*if (depends.length) {
            new Model(this.fields_view.fields.dependencies_id.relation).call("read", [depends, ['name','id']]).done(function(datas) {
            	_.each(datas, function (data) {
                	console.log('tHE datAS', data);
                	child_cnx[data.id] = data.name;
                });                
            });
        }*/
        console.log('ReMaPed', depends, this.fields_view.fields.dependencies_id.relation, child_cnx);
        
        // links:
        var links =[];        
        _.each(this.data.records, function (record) {
        	if (record.dependencies_id.length) {
        		var rez = [], deps = [], recs = [];
        		_.each(record.dependencies_id, function (targetid) { // per child dependency
        			var target_name = child_cnx[targetid];// id2index.indexOf(targetid),
        			if (target_name) {
        				var target_idx = names.indexOf(target_name);
	        			var	source_idx = id2index.indexOf(record.id);
	        			deps.push(targetid);
	        			if (	source_idx != target_idx
	        					&& $.isNumeric( target_idx ) 
	        					&& (target_idx !== -1)
	        					&& $.isNumeric( source_idx )
	        					&& (source_idx !== -1)
	        					) {
	            			rez.push(target_idx);
	            			recs.push(record.id);
		        			links.push({
		        				'source': source_idx, 
		        				'target': target_idx, 
		        				'value':1 });
		        			//console.log('linked:', names[source_idx], '>', names[target_idx]);
	        			}
        			}
        		});
        		//console.log("DEPS=", rez, deps, recs);
        	}
        });
        //console.log('lINKs', links);
        links.forEach(function(link) {
            var source = nodes[link.source]
              , target = nodes[link.target]

            source.children = source.children || []
            source.children.push(link.target)

            target.parents = target.parents || []
            target.parents.push(link.source)
        })
        
        
      //Set up the colour scale
        var color = d3.scale.category20();
        
        var groups = nodes.reduce(function(groups, file) {
            var group = file.mgroup || 'none'
              , index = groups.indexOf(group)

            if (index === -1) {
                index = groups.length
                groups.push(group)
            }

            file.group = index

            return groups
        }, [])

        groups = groups.map(function(name, n) {
            var color = d3.hsl(n / groups.length * 300, 0.7, 0.725)

            return {
                  name: name
                , color: color.toString()
            };
        })


      //Creates the graph data structure out of the json data
        this.d3force
            //.gravity(1)
            .linkDistance(20)
            .charge(-50)
            //.linkStrength(function(x) {	return x.weight * 10})
        	.nodes(nodes)
            .links(links)
            .start();
        
      //Create all the line svgs but without locations yet
        /*var link = this.svg.selectAll(".link")
            .data(links)
            .enter().append("line")
            .attr("class", "link")
            .style("marker-end",  "url(#end-arrow)") //Added 
            ;*/
        var link = this.svg.selectAll('path') //.selectAll(".link")
	        .data(links)
	        .enter().append("path")
	        .attr("class", "link")
	        .style("marker-end",  "url(#end-arrow)") //Added 
	        ;
        var textTarget = false;
        var colors = {
        	      links: 'FAFAFA'
        	    , text: {
        	        subtitle: 'FAFAFA'
        	    }
        	    , nodes: {
        	        method: function(d) {
        	            return groups[d.group].color
        	        }
        	        , hover: 'FAFAFA'
        	        , dep: '252929'
        	    }
        	}
        //Do the same with the circles for the nodes - no 
        var node = this.svg.selectAll(".node")
            .data(nodes, function(d) { return d.name })
            .enter().append("circle")
            .attr("class", "node")
            .attr('cx', function(d) { return d.x })
            .attr('cy', function(d) { return d.y })
            .attr("r", function(d) {
                return d.app ? 8 : 4;
            })
            .style("fill", function (d) {
	            return color(d.group);
	        })
            .call(this.d3force.drag)//;
            .on('mouseover', function(d) {
        textTarget = d

        text.attr('transform', 'translate(' + d.x + ',' + d.y + ')')
            .text(d.name)
            .style('display', null)

        d3.select(this)
          .style('fill', colors.nodes.hover)

        d3.selectAll(childNodes(d))
            .style('fill', colors.nodes.hover)
            .style('stroke', colors.nodes.method)
            .style('stroke-width', 2)

        d3.selectAll(parentNodes(d))
            .style('fill', colors.nodes.dep)
            .style('stroke', colors.nodes.method)
            .style('stroke-width', 2)
    })
    .on('mouseout', function(d) {
        textTarget = false

        text.style('display', 'none')

        d3.select(this)
          .style('fill', colors.nodes.method)

        d3.selectAll(childNodes(d))
            .style('fill', colors.nodes.method)
            .style('stroke', null)

        d3.selectAll(parentNodes(d))
            .style('fill', colors.nodes.method)
            .style('stroke', null)
    })
    .on('click', function(d) {
        if (focus === d) {
            self.d3force.charge(-50)// * colony.scale)
                 .linkDistance(20)// * colony.scale)
                 .linkStrength(1)
                 .start()

            node.style('opacity', 1)
            link.style('opacity', function(d) {
                return d.target.module ? 0.2 : 0.3
            })

            focus = false

            /*d3.select('#readme-contents')
              .html(readme)
              .classed('showing-code', false)
            */

            return
        }

        focus = d
		/*
        d3.xhr('./files/' + d.filename + '.html', function(res) {
            if (!res) return

            d3.select('#readme-contents')
              .html(res.responseText)
              .classed('showing-code', true)

            document.getElementById('readme')
                    .scrollTop = 0
        })*/
		

        node.style('opacity', function(o) {
            o.active = connected(d, o)
            return o.active ? 1 : 0.2
        })

        self.d3force.charge(function(o) {
            return (o.active ? -100 : -5) //* colony.scale
        }).linkDistance(function(l) {
            return (l.source.active && l.target.active ? 100 : 20) //* colony.scale
        }).linkStrength(function(l) {
            return (l.source === d || l.target === d ? 1 : 0) //* colony.scale
        }).start()

        link.style('opacity', function(l, i) {
            return l.source.active && l.target.active ? 0.2 : 0.02
        })
    })
    
    var vis = this.svg;
    text = vis.selectAll('.nodetext')
    .data([
          [-1.5,  1.5,  1] // "Shadows"
        , [ 1.5,  1.5,  1]
        , [-1.5, -1.5,  1]
        , [ 1.5, -1.5,  1]
        , [ 0.0,  0.0,  0] // Actual Text
    ])
  .enter()
    //.insert('text', ':last-child')
    .append('text')
    .attr('class', 'nodetext')
    .classed('shadow', function(d) { return d[2] })
    .attr('dy', function(d) { return d[0] - 10 })
    .attr('dx', function(d) { return d[1] })
    .attr('text-anchor', 'middle')

function refresh(e) {
    width = Math.max(window.innerWidth * 0.5, 500)
    height = window.innerHeight

    force.size([width, height])
         .resume()

    vis.attr('width', window.innerWidth)
       .attr('height', height)
};

function childNodes(d) {
    if (!d.children) return []

    return d.children
        .map(function(child) {
            return node[0][child]
        }).filter(function(child) {
            return child
        })
};

function parentNodes(d) {
    if (!d.parents) return []

    return d.parents
        .map(function(parent) {
            return node[0][parent]
        }).filter(function(parent) {
            return parent
        })
};

function connected(d, o) {
    return o.index === d.index ||
        (d.children && d.children.indexOf(o.index) !== -1) ||
        (o.children && o.children.indexOf(d.index) !== -1) ||
        (o.parents && o.parents.indexOf(d.index) !== -1) ||
        (d.parents && d.parents.indexOf(o.index) !== -1)
};
      //Now we are giving the SVGs co-ordinates - the force layout is generating the co-ordinates which this code is using to update the attributes of the SVG elements
        this.d3force.on("tick", function () {
            /*link.attr("x1", function (d) {
                return d.source.x;
            })
                .attr("y1", function (d) {
                return d.source.y;
            })
                .attr("x2", function (d) {
                return d.target.x;
            })
                .attr("y2", function (d) {
                return d.target.y;
            });*/
        	link.attr("d", function (d) {
        		var deltaX = d.target.x - d.source.x,
                deltaY = d.target.y - d.source.y,
                dist = Math.sqrt(deltaX * deltaX + deltaY * deltaY),
                normX = deltaX / dist,
                normY = deltaY / dist,
                sourcePadding = 6,//d.source.r,// d.left ? 17 : 12,
                targetPadding = 6,//d.target.r, //d.right ? 17 : 12,
                sourceX = d.source.x + (sourcePadding * normX),
                sourceY = d.source.y + (sourcePadding * normY),
                targetX = d.target.x - (targetPadding * normX),
                targetY = d.target.y - (targetPadding * normY);
        		/*if (deltaX = deltaY)
        		console.log(deltaX, deltaY,
        				sourceX, sourceY,
        				targetX, targetY);*/
        		return 'M' + sourceX + ',' + sourceY + 'L' + targetX + ',' + targetY;
            });

            node.attr("cx", function (d) {
                return d.x;
            })
                .attr("cy", function (d) {
                return d.y;
            });
        });
        
        $('svg').appendTo(this.$el);
        // add empty invisible divs to make sure that all kanban records are left aligned
        for (var i = 0, ghost_div; i < 6; i++) {
            ghost_div = $("<div>").addClass("o_kanban_record o_kanban_ghost");
            ghost_div.appendTo(fragment);
        }
        //this.postprocess_m2m_tags();
    },
    
    has_active_field: function() {
        return this.fields_view.fields.active;
    },
    _is_quick_create_enabled: function() {
        if (!this.quick_creatable || !this.is_action_enabled('create'))
            return false;
        if (this.fields_view.arch.attrs.quick_create !== undefined)
            return JSON.parse(this.fields_view.arch.attrs.quick_create);
        return !!this.grouped;
    },
    
    get_column_options: function () {
        return {
            editable: this.is_action_enabled('group_edit'),
            deletable: this.is_action_enabled('group_delete'),
            has_active_field: this.has_active_field(),
            grouped_by_m2o: this.grouped_by_m2o,
            relation: this.relation,
            qweb: this.qweb,
            fields: this.fields_view.fields,
            quick_create: this._is_quick_create_enabled(),
        };
    },

    render_grouped: function (fragment) {
        var self = this;
        var record_options = _.extend(this.record_options, {
            draggable: true,
        });

        var column_options = this.get_column_options();

        _.each(this.data.groups, function (group) {
            var column = new KanbanColumn(self, group, column_options, record_options);
            column.appendTo(fragment);
            self.widgets.push(column);
        });
        this.$el.sortable({
            axis: 'x',
            items: '> .o_kanban_group',
            handle: '.o_kanban_header',
            cursor: 'move',
            revert: 150,
            delay: 100,
            tolerance: 'pointer',
            forcePlaceholderSize: true,
            stop: function () {
                var ids = [];
                self.$('.o_kanban_group').each(function (index, u) {
                    ids.push($(u).data('id'));
                });
                self.resequence(ids);
            },
        });
        if (this.is_action_enabled('group_create') && this.grouped_by_m2o) {
            this.column_quick_create = new ColumnQuickCreate(this);
            this.column_quick_create.appendTo(fragment);
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
        this.$el.delegate('.circleview-td span, .circleview-tr span', 'click', function (e) {
            e.stopImmediatePropagation();
            self.activate($(this).closest('tr').data('id'));
        });

        this.$el.delegate('.circleview-tr', 'click', function () {
            var is_loaded = 0,
                $this = $(this),
                record_id = $this.data('id'),
                row_parent_id = $this.data('row-parent-id'),
                record = self.records[record_id],
                children_ids = record[self.children_field];

            _(children_ids).each(function(childid) {
                if (self.$el.find('[id=circlerow_' + childid + '][data-row-parent-id='+ record_id +']').length ) {
                    if (self.$el.find('[id=circlerow_' + childid + '][data-row-parent-id='+ record_id +']').is(':hidden')) {
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
            var $curr_node = self.$el.find('#circlerow_' + id);
            var children_rows = QWeb.render('CircleView.rows', {
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
        return this.rpc('/web/circleview/action', {
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
            var $child_row = this.$el.find('[id=circlerow_' + child_id + '][data-row-parent-id='+ curnode.data('id') +']');
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

core.view_registry.add('circle', CircleView);

return CircleView;

});

