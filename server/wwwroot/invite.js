const token = location.hash.slice(1);
history.replaceState(null, '', location.pathname);
const input = document.getElementById('invite-token');
if (input) input.value = token;
