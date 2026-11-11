let data, visible=20;
const money=n=>new Intl.NumberFormat('en-GB',{style:'currency',currency:'GBP',maximumFractionDigits:0}).format(n||0);
const title=s=>s.replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase());
function bars(id,items){const target=document.getElementById(id), max=Math.max(...Object.values(items));target.innerHTML=Object.entries(items).sort((a,b)=>b[1]-a[1]).slice(0,6).map(([label,value])=>`<div class="bar-row"><span class="bar-label">${title(label)}</span><div class="track"><div class="fill" style="width:${value/max*100}%"></div></div><span class="bar-value">${value}</span></div>`).join('')}
function priorityTag(p){return `<span class="priority"><i class="dot ${p}"></i>${title(p)}</span>`}
function render(){const search=document.getElementById('search').value.trim();const buyer=document.getElementById('buyerFilter').value;const priority=document.getElementById('priorityFilter').value;let rows=data.records.filter(r=>(!search||String(r.customer_id).includes(search))&&(buyer==='all'||r.buyer_type===buyer)&&(priority==='all'||r.retention_priority===priority));rows.sort((a,b)=>({high:0,medium:1,low:2,none:3}[a.retention_priority]-{high:0,medium:1,low:2,none:3}[b.retention_priority])||b.lifetime_revenue-a.lifetime_revenue);document.getElementById('resultCount').textContent=`Showing ${Math.min(visible,rows.length)} of ${rows.length.toLocaleString()} customers`;document.getElementById('customerRows').innerHTML=rows.slice(0,visible).map(r=>`<tr><td><strong>${r.customer_id}</strong>${priorityTag(r.retention_priority)}</td><td>${title(r.buyer_type)}<span class="sub">${title(r.value_segment)} · ${r.order_count} orders</span></td><td>${title(r.lifecycle_stage)}<span class="sub">${r.days_since_last_order} days since last order</span></td><td><span class="tag">${title(r.preferred_category)}</span></td><td><strong>${r.primary_offer}</strong><span class="sub">${title(r.offer_type)}</span></td><td>${r.discount?`${Math.round(r.discount*100)}%`:'—'}</td><td><strong>${money(r.lifetime_revenue)}</strong><span class="sub">AOV ${money(r.average_order_value)}</span></td></tr>`).join('');document.getElementById('showMore').style.display=visible>=rows.length?'none':'block'}
fetch('dashboard-data.json').then(r=>r.json()).then(d=>{
  data=d;
  document.getElementById('analysisDate').textContent=d.analysis_date;
  document.getElementById('customerCount').textContent=d.summary.customers.toLocaleString();
  document.getElementById('revenue').textContent=money(d.summary.revenue);
  document.getElementById('priorityCount').textContent=d.summary.high_priority;
  document.getElementById('bulkCount').textContent=d.summary.bulk_candidates;
  document.getElementById('simAcceptance').textContent=`${Math.round(d.simulation.acceptance_rate*100)}%`;
  document.getElementById('simRedemption').textContent=`${Math.round(d.simulation.redemption_rate*100)}%`;
  document.getElementById('simRevenue').textContent=money(d.simulation.simulated_follow_up_revenue_gbp);
  document.getElementById('simProfit').textContent=money(d.simulation.simulated_net_gross_profit_gbp);
  document.getElementById('qualityStatus').textContent=`Backend checks: ${d.quality_status}`;
  document.getElementById('offerPerformance').innerHTML=d.top_simulated_offers.map(o=>`<div class="performance-row"><span>${o.offer_name}</span><span>${Math.round(o.redemption_rate*100)}%</span></div>`).join('');
  bars('lifecycleBars',d.lifecycle_counts);
  bars('categoryBars',d.category_counts);
  ['search','buyerFilter','priorityFilter'].forEach(id=>document.getElementById(id).addEventListener('input',()=>{visible=20;render()}));
  document.getElementById('showMore').addEventListener('click',()=>{visible+=20;render()});
  render();
}).catch(()=>document.querySelector('.shell').innerHTML='<p>Dashboard data could not be loaded.</p>');
