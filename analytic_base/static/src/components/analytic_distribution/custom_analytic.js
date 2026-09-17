/** @odoo-module **/

import { registry } from "@web/core/registry";
import { AnalyticDistribution } from '@analytic/components/analytic_distribution/analytic_distribution';

export class AnalyticDistributionInherit extends AnalyticDistribution {
    async formatData(nextProps) {
        const data = nextProps.value;
        const analytic_account_ids = Object.keys(data).map((id) => parseInt(id));
        const records = analytic_account_ids.length ? await this.fetchAnalyticAccounts([["id", "in", analytic_account_ids]]) : [];
        if (records.length < data.length) {
            console.log('removing tags... value should be updated');
        }
        let widgetData = Object.assign({}, ...this.allPlans.map((plan) => ({[plan.id]: {...plan, distribution: []}})));
        records.map((record) => {
            if (!widgetData[record.root_plan_id[0]]) {
                // plans might not have been retrieved
                widgetData[record.root_plan_id[0]] = { distribution: [] }
            }
            widgetData[record.root_plan_id[0]].distribution.push({
                analytic_account_id: record.id,
                percentage: data[record.id],
                percentage_amount: (this.props.record.data.price_subtotal/100) * data[record.id],
                id: this.nextId++,
                group_id: record.root_plan_id[0],
                analytic_account_name: record.name,
                color: record.color,
            });
        });

        this.state.list = widgetData;
    }

    async percentageChanged(dist_tag, ev) {
        dist_tag.percentage = this.parse(ev.target.value);
        dist_tag.percentage_amount = dist_tag.percentage * (this.props.record.data.price_subtotal/100)
        // console.log("THIS PROPS");
        // console.log(this.props);
        // console.log("SUBTOTAL");
        // console.log(this.props.record.data.price_subtotal)
        // console.log("LIST")
        // console.log(this.list)

        if (this.remainderByGroup(dist_tag.group_id)) {
            this.setFocusSelector(`#plan_${dist_tag.group_id} .incomplete .o_analytic_account_name`);
        }
        this.autoFill();
    }

    async percentageAmountChanged(dist_tag, ev) {
        dist_tag.percentage_amount = this.parse(ev.target.value);
        dist_tag.percentage = 100 * (dist_tag.percentage_amount / this.props.record.data.price_subtotal)
        // console.log("THIS PROPS");
        // console.log(this.props);
        // console.log("SUBTOTAL");
        // console.log(this.props.record.data.price_subtotal)
        // console.log("LIST")
        // console.log(this.list)

        if (this.remainderByGroup(dist_tag.group_id)) {
            this.setFocusSelector(`#plan_${dist_tag.group_id} .incomplete .o_analytic_account_name`);
        }
        this.autoFill();
    }

    newTag(group_id) {
        return {
            id: this.nextId++,
            group_id: group_id,
            analytic_account_id: null,
            analytic_account_name: "",
            percentage: this.remainderByGroup(group_id),
            percentage_amount: (this.props.record.data.price_subtotal/100) * this.remainderByGroup(group_id),
            color: this.list[group_id].color,
        }
    }
}

registry.category("fields").add("analytic_distribution_inherit", AnalyticDistributionInherit);
