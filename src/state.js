export const state = { view: 'home', selectedTicket: null, tickets: [
  { id: 'RF-4821', customer_name: 'Maya Rahman', device_info: 'MacBook Air M2', status: 'in_progress', created_at: 'Today' },
  { id: 'RF-4819', customer_name: 'Arif Hossain', device_info: 'Dell XPS 13', status: 'waiting_parts', created_at: 'Yesterday' },
  { id: 'RF-4814', customer_name: 'Sadia Islam', device_info: 'HP Pavilion 15', status: 'completed', created_at: 'Sep 4' },
] };
export const navigate = (view) => { state.view = view; };
