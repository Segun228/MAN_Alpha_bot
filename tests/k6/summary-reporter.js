import { textSummary } from "https://jslib.k6.io/k6-summary/0.0.4/index.js";

export default function handleSummary(data) {
    const scenarioName = __ENV.SCENARIO || 'default_scenario';
    const reportFilename = `tests/k6/results/${scenarioName}_summary.json`;

    console.log(`Finished running scenario: ${scenarioName}`);
    console.log(`Report will be saved to: ${reportFilename}`);

    return {
        'stdout': textSummary(data, { indent: ' ', enableColors: true }),
        [reportFilename]: JSON.stringify(data, null, 2),
    };
}