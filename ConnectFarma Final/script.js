function showLogin(type) {
  document.getElementById('consumerForm').style.display = 'none';
  document.getElementById('farmerForm').style.display = 'none';
  document.getElementById('choiceContainer').style.display = 'none';
  document.getElementById('backBtn').style.display = 'block';

  if (type === 'consumer') {
    document.getElementById('consumerForm').style.display = 'flex';
  } else if (type === 'farmer') {
    document.getElementById('farmerForm').style.display = 'flex';
  }
}

function goBack() {
  document.getElementById('consumerForm').style.display = 'none';
  document.getElementById('farmerForm').style.display = 'none';
  document.getElementById('choiceContainer').style.display = 'flex';
  document.getElementById('backBtn').style.display = 'none';

  document.getElementById('consumerUsername').value = '';
  document.getElementById('consumerPassword').value = '';
  document.getElementById('farmerUsername').value = '';
  document.getElementById('farmerPassword').value = '';
}

function handleLogin(event, type) {
  event.preventDefault();
  const username = document.getElementById(`${type}Username`).value;
  const password = document.getElementById(`${type}Password`).value;
  alert("Your login is done. This is a demo.");
}
