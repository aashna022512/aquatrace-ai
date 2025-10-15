// Small pop sound on Identify
const identifyBtn = document.getElementById('identifyBtn');
const imageInput  = document.getElementById('imageUpload');
const resultDiv   = document.getElementById('result');

let pop;
try {
  pop = new Audio('assets/pop.mp3');
  pop.volume = 0.2;
} catch (e) {
  // no-op if not found
}

function show(html){
  resultDiv.innerHTML = html;
  resultDiv.style.opacity = '0';
  requestAnimationFrame(()=>{ resultDiv.style.transition='opacity .25s'; resultDiv.style.opacity='1' });
}

// Simple fake demo (replace with real backend later)
function fakeDetect(name=''){
  const n = name.toLowerCase();
  if (n.includes('shark'))  return { species:'Blue Shark', endangered:'Near Threatened', fun:'Great travelers of the ocean.' };
  if (n.includes('turtle')) return { species:'Green Sea Turtle', endangered:'Endangered', fun:'Can hold breath for hours.' };
  return { species:'Unknown', endangered:'Unknown', fun:'Use AI backend to detect accurately.' };
}

if (identifyBtn){
  identifyBtn.addEventListener('click', async (e)=>{
    e.preventDefault();
    if (pop){ try{ pop.currentTime = 0; pop.play(); }catch(_){} }

    const file = imageInput?.files?.[0];
    if (!file){
      show(`<p style="color:#ffdca8">Please choose an image first.</p>`);
      return;
    }

    show(`⏳ Identifying...`);
    await new Promise(r=>setTimeout(r, 700));

    const r = fakeDetect(file.name);
    show(`
      <h3>🐟 Species: ${r.species}</h3>
      <p><strong>Endangered:</strong> ${r.endangered}</p>
      <p><strong>Fun fact:</strong> ${r.fun}</p>
      <img alt="preview" src="${URL.createObjectURL(file)}" />
    `);
  });
}
