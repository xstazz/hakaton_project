function checkScroll() {
    const danielImg = document.querySelector('.top-fixed img');
    const scrollPosition = window.scrollY;
    
    const danielImgHeight = 200; 
    
    if (scrollPosition > danielImgHeight) {
    document.documentElement.removeEventListener("mousemove", trackMouse);
    document.documentElement.style.setProperty('--blur-effect', 'none');
    } else {
    document.documentElement.addEventListener("mousemove", trackMouse);
    document.documentElement.style.setProperty('--blur-effect', 'blur(10px)');
    }
    }
    
    window.addEventListener('scroll', checkScroll);
    
    window.addEventListener('load', checkScroll);
    
    function trackMouse(e) {
    const pos = document.documentElement;
    pos.style.setProperty('--x', e.clientX + "px");
    pos.style.setProperty('--y', e.clientY + "px");
    }
    