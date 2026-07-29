document.addEventListener("DOMContentLoaded", () => {
const STORAGE_KEY = "threads-read"

function getReadThreads(){
    try {
        const raw = localStorage.getItem(STORAGE_KEY)
        return raw ? JSON.parse(raw) : []
    } catch {
        return []
    }
}

function saveReadThreads(list){
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
}

function isRead(uid){
    const list = getReadThreads()
    return list.includes(uid)
}

function markRead(uid){
    const list = getReadThreads()
    if(!list.includes(uid)){
        list.push(uid)
        saveReadThreads(list)
    }
}

function markUnread(uid){
    let list = getReadThreads()
    list = list.filter(id => id !== uid)
    saveReadThreads(list)
}

function applyReadState(){
    const list = getReadThreads()
    document.querySelectorAll("[data-uid]").forEach(el => {
        const uid = el.dataset.uid
        if(list.includes(uid)){
            el.dataset.read = "true"
        } else {
            el.dataset.read = "false"
        }
    })
}

function openReadCongrats(count){
    const modal = document.getElementById("modal-root")
    const modalTitle = document.getElementById("modal-title")
    const modalText = document.getElementById("modal-text")
    const modalMedia = document.getElementById("modal-media")
    const modalCopy = document.getElementById("modal-copy")
    if(!modal) return

    const btn = document.getElementById("mark-read-btn")
    const congratsTitle = btn?.dataset?.congratsTitle || "تبریک 🎉"
    const congratsText = btn?.dataset?.congratsText || `تا الان ${count} ترد خوندی 👏`
    const congratsImage = btn?.dataset?.congratsImage || ""

    modalTitle.textContent = congratsTitle
    modalText.textContent = congratsText.replace("{count}", count)
    if(congratsImage && modalMedia){
        modalMedia.innerHTML = `<img src="${congratsImage}">`
    }

    if(modalCopy){
        modalCopy.classList.add("hidden")
    }
    modal.classList.remove("hidden")
}

const btn = document.getElementById("mark-read-btn")

if(btn){
    const uid = btn.dataset.uid

    function updateButton(){
        const markText = btn.dataset.markText || "خواندی؟ کلیک کن"
        const unmarkText = btn.dataset.unmarkText || "خوانده نشده"
        if(isRead(uid)){
            btn.textContent = unmarkText
        }else{
            btn.textContent = markText
        }
    }

    updateButton()

    btn.addEventListener("click", () => {
        const wasRead = isRead(uid)
        if(wasRead){
            markUnread(uid)
        }else{
            markRead(uid)
        }
        applyReadState()
        updateButton()
        if(!wasRead){
            const count = getReadThreads().length
            openReadCongrats(count)
        }
    })
}

applyReadState()
})
