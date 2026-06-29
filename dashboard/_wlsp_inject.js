const fs = require('fs');
const F = process.argv[2];
const raw = fs.readFileSync(F, 'utf8');
const wrap = JSON.parse(raw);
const text = wrap.result[0].text; // python-repr string: [{'doc': '...'}]
const marker = "'doc': '";
const start = text.indexOf(marker) + marker.length;
const end = text.lastIndexOf("'");
let doc = text.slice(start, end);
doc = doc.replace(/\\(.)/g, (m, c) => c === 'n' ? '\n' : c === 't' ? '\t' : c === 'r' ? '\r' : c);
const obj = JSON.parse(doc); // validates JSON
const pretty = JSON.stringify(obj, null, 2);

const htmlPath = 'leakage_dashboard.html';
let html = fs.readFileSync(htmlPath, 'utf8');
const A = '<!-- WLSP_DATA_START -->';
const B = '<!-- WLSP_DATA_END -->';
const i = html.indexOf(A) + A.length;
const j = html.indexOf(B);
if (i < A.length || j < 0) throw new Error('markers not found');
const block = '\n<script>\nconst dashboardData = ' + pretty + ';\nwindow.dashboardData = dashboardData;\n</script>\n';
html = html.slice(0, i) + block + html.slice(j);
fs.writeFileSync(htmlPath, html);

const c = obj.summary.counts, d = obj.summary.displayed;
console.log('WROTE bytes', html.length);
console.log('l1', obj.l1.length, 'l2', obj.l2.length, 'l3', obj.l3.length, 'l4', obj.l4.length, 'l5', obj.l5.length);
console.log('counts', JSON.stringify(c));
console.log('displayed', JSON.stringify(d));
console.log('ph_count', obj.summary.ph_count, 'ph_summary_rows', obj.ph_summary.length);
console.log('account_summary', JSON.stringify(obj.account_summary));
const unattr = [].concat(obj.l1, obj.l2, obj.l3, obj.l4).filter(r => r.ph === 'UNATTRIBUTED');
const withStatus = unattr.filter(r => r.ph_status);
console.log('unattr_rows', unattr.length, 'with_ph_status', withStatus.length,
  'RECOVERABLE', unattr.filter(r => r.ph_status === 'RECOVERABLE').length,
  'MISSING_SOURCE', unattr.filter(r => r.ph_status === 'MISSING_SOURCE').length);
console.log('l5_declining_phs', [...new Set(obj.l5.filter(r => r.declining === true).map(r => r.ph))].sort().join(','));
