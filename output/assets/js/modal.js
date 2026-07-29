const modal = document.getElementById("modal-root")
const modalTitle = document.getElementById("modal-title")
const modalText = document.getElementById("modal-text")
const modalMedia = document.getElementById("modal-media")
const modalSocial = document.getElementById("modal-social")
const modalCopy = document.getElementById("modal-copy")
const modalClose = document.getElementById("modal-close")
const modalLinkPreview = document.getElementById("modal-link-preview")
const modalLinkUrl = document.getElementById("modal-link-url")

let copyValue = ""

function renderSocialLinks(json) {
  if (!json) { modalSocial.innerHTML = ""; modalSocial.classList.add("hidden"); return }
  try {
    const links = JSON.parse(json)
    if (!Array.isArray(links) || links.length === 0) { modalSocial.classList.add("hidden"); return }
    modalSocial.innerHTML = links.map(link =>
      `<a href="${link.url}" target="_blank" class="social-tag">${link.name}</a>`
    ).join("")
    modalSocial.classList.remove("hidden")
  } catch(e) {
    console.error("خطا در پارس کردن لینک‌های اجتماعی:", e)
    modalSocial.classList.add("hidden")
  }
}

function stopModalMedia(){
  const media = modalMedia.querySelectorAll("video, audio")
  media.forEach(m => {
    m.pause()
    m.currentTime = 0   
  })

  modalMedia.innerHTML = ""; 
}

function resetCopyButton(){
  const copyText = modalCopy.dataset.copyText || "کپی لینک"
  modalCopy.textContent = copyText
  modalCopy.classList.remove("copied")
}

document.querySelectorAll("[data-modal]").forEach(el => {
  el.addEventListener("click", function(e){
    e.preventDefault()
    const type = this.dataset.modalType
    const src = this.dataset.src
    modalTitle.textContent = this.dataset.modalTitle || ""
    modalText.textContent = this.dataset.modalText || ""
    modalMedia.innerHTML = ""
    modalCopy.classList.add("hidden")
    modalLinkPreview.classList.add("hidden")
    renderSocialLinks(this.dataset.modalSocial)

    if(type === "image"){
      modalMedia.innerHTML = `<img src="${src}" />`
    }
    if(type === "video"){
      modalMedia.innerHTML = `<video controls src="${src}"></video>`
    }
    if(type === "audio"){
      modalMedia.innerHTML = `<audio controls src="${src}"></audio>`
    }
    if(type === "iframe")
    {
      modalMedia.innerHTML = `
        <iframe 
          src="${src}" 
          frameborder="0" 
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
          allowfullscreen 
          style="width: 100%; aspect-ratio: 16/9; border-radius: 8px;">
        </iframe>`
    }
    if(type === "share"){
      copyValue = src
      modalLinkPreview.classList.remove("hidden")
      modalLinkUrl.textContent = src
      modalLinkUrl.href = src
      modalCopy.classList.remove("hidden")
      resetCopyButton()
    }
    modal.classList.remove("hidden")
  })
})

modalCopy.addEventListener("click", ()=>{
  const text = modalText.textContent
  const link = copyValue
  const fullText = text + "\n" + link
  navigator.clipboard.writeText(fullText).then(() => {
    const copiedText = modalCopy.dataset.copiedText || "کپی شد"
    modalCopy.textContent = copiedText
    modalCopy.classList.add("copied")
    setTimeout(()=>{
      resetCopyButton()
    }, 2000)
  }).catch(err => {
    console.error("خطا در کپی کردن:", err)
  })
})

modalClose.addEventListener("click", ()=>{
  stopModalMedia()     
  modal.classList.add("hidden")
})

modal.addEventListener("click", (e)=>{
  if(e.target === modal){
    stopModalMedia()  
    modal.classList.add("hidden")
  }
})
