const body = document.getElementById("container");
const message = document.getElementById("message");

setTimeout(() => {
  if (body.contains(message)) {
    message.style.transform = "translateY(-60px)";
    setTimeout(() => {
      body.removeChild(message);
    }, 1000);
  }
}, 5000);


