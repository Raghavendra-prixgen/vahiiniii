/** @odoo-module **/

import { Component, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";

// console.log("Loading Production Analytics Module......................");

// Main Dashboard Widget Component
class ProductionAnalyticsWidget extends Component {
    static template = "production_analytics.ProductionAnalyticsDashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        onWillStart(async () => {
            var source_id = parseInt(this.env.searchModel.globalContext.active_id);
            // console.log(source_id,"................................")

            this.dashboardData = await this.orm.call("prix.mrp.report", "retrieve_dashboard", [source_id]);
            // console.log("this.dashboardData--------------------",this.dashboardData);
            
        })
    }
}

// Enhanced List Renderer for Production Analytics
class ProductionAnalyticsListRenderer extends ListRenderer {
    static template = "production_analytics.ProductionAnalyticsListView";
    static components = {
        ...ListRenderer.components,
        ProductionAnalyticsWidget,
    };

    setup() {
        super.setup();
        // console.log("ProductionAnalyticsListRenderer setup------------------------");
    }
}

// Production Analytics List View Configuration
const productionAnalyticsListView = {
    ...listView,
    Renderer: ProductionAnalyticsListRenderer,
};

// Register the new view
registry.category("views").add("production_analytics_list_view", productionAnalyticsListView);

// console.log("Production Analytics Module Loaded Successfully___________________________________");