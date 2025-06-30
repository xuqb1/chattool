document.addEventListener('DOMContentLoaded', function() {
    const welcomeDiv = document.getElementById('welcomeDiv');
    welcomeDiv.style.display = ''
    const chatContainer = document.getElementById('chatContainer');
    chatContainer.style.display = 'none'
    const sidebar = document.getElementById('sidebar');
    if(sidebar){
      sidebar.style.transform = 'translateX(0px)';
    }
});
//let meChatId = 0;
//let meChat = []
function addChatContent(from, content, id){
  const welcomeDiv = document.getElementById('welcomeDiv');
  welcomeDiv.style.display = 'none'
  const chatContainer = document.getElementById('chatContainer');
  chatContainer.style.display = ''
  const messageElement = document.createElement('div');
  if(from == 'me'){
    messageElement.className = 'message me';
    messageElement.id = 'me' + id;
    const userElement = document.createElement('div');
    userElement.className = 'user';
    userElement.innerHTML = decodeURIComponent(content);
    messageElement.appendChild(userElement);
  } else {
    messageElement.className = 'message bot';
    messageElement.innerHTML = decodeURIComponent(content);
  }
  chatContainer.appendChild(messageElement);
}
function addMyChatList(id, content){
  const myChatList = document.getElementById('myChatList')
  let li = document.createElement('li')
  let a = document.createElement('a')
  a.href = '#me' + id
  str = decodeURIComponent(content)
  //if(str.indexOf('\n')>=0){
  //  str = str.replace(/\n/g, "")
  //  alert(str)
  //}
  if(str.length > 50){
    str = str.substring(0, 50) + ' ...'
  }
  //a.textContent = str;
  a.innerHTML = str;
  li.appendChild(a)
  myChatList.appendChild(li)
}

function toggleSidebar(obj) {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');
    const chatContainer = document.getElementById('chatContainer');
    if (sidebar.style.transform === 'translateX(0px)') {
        sidebar.style.transform = 'translateX(100%)';
        mainContent.style.marginRight = '0px';
        chatContainer.style.marginRight = '0px';
        obj.textContent = '<';
    } else {
        sidebar.style.transform = 'translateX(0px)';
        mainContent.style.marginRight = '200px';
        chatContainer.style.marginRight = '200px';
        obj.textContent = '>';
    }
}

function totopdown(){
  const chatContainer = document.getElementById('chatContainer');
  const obj = document.getElementById('updownDiv')
  console.log()
  if(obj.textContent === '<'){
    document.body.scrollTo(0, 0);
    obj.textContent = '>'
  }else{
    obj.textContent = '<'
    document.body.scrollTo(0, document.body.scrollHeight)
  }
}
function todown(){
  const obj = document.getElementById('updownDiv')
  obj.textContent = '<'
  document.body.scrollTo(0, document.body.scrollHeight)
}
// JavaScript函数来控制折叠和展开
function toggleCode(button) {
    var codeBlock = button.parentNode.parentNode.querySelector('pre');
    if (codeBlock.style.display === 'none') {
        codeBlock.style.display = 'block';
        button.className = 'toggle-div arrowUp';
    } else {
        codeBlock.style.display = 'none';
        button.className = 'toggle-div arrowDown';
    }
}