(() => {
  "use strict";
  const page=document.querySelector(".for-login"); if(!page) return;
  const esc=value=>String(value||"").replace(/[&<>'"]/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[ch]));
  async function call(method,args={}) { const response=await frappe.call({method,args}); return response.message||{}; }
  function standardSocialAndSignupRemain() {
    // Frappe itself renders enabled social providers, signup, forgot-password,
    // magic-link and LDAP controls. The design only styles visible standard DOM.
    document.documentElement.dataset.qorgLoginStandardOptions="1";
  }
  async function setLanguage(language){ await call("qorg.qorg.design_system.api.set_login_language",{language}); location.reload(); }
  function mountLanguage(config,host){
    if(!config.show_login_language_switcher || !(config.languages||[]).length) return;
    const wrap=document.createElement("label"); wrap.className="qorg-login-language"; wrap.innerHTML=`<span class="sr-only">${esc(__("Language"))}</span><span aria-hidden="true">${frappe.utils.icon("globe","sm")}</span>`;
    const select=document.createElement("select"); select.setAttribute("aria-label",__("Language"));
    for(const item of config.languages){const option=document.createElement("option");option.value=item.language_code;option.textContent=item.language_name;option.selected=item.language_code===config.current_language;select.append(option)}
    select.addEventListener("change",()=>setLanguage(select.value)); wrap.append(select); host.append(wrap);
  }
  function apply(config){
    if(!config.enable_login_experience) return;
    document.documentElement.dataset.qorgLoginExperience="1";
    const wrapper=document.createElement("div"); wrapper.className="qorg-login-shell";
    const visual=document.createElement("section"); visual.className=`qorg-login-visual qorg-overlay-${String(config.login_overlay_strength||"Medium").toLowerCase()} qorg-text-${String(config.login_text_color||"Light").toLowerCase()}`;
    if(config.login_background_image){visual.style.setProperty("--qorg-login-image",`url(${JSON.stringify(String(config.login_background_image))})`)}
    visual.dataset.position=String(config.login_background_position||"Center").toLowerCase();
    visual.innerHTML=`<div class="qorg-login-visual__content">${config.login_brand_logo?`<img class="qorg-login-visual__logo" src="${esc(config.login_brand_logo)}" alt="">`:""}<h1>${esc(config.login_visual_title)}</h1><p>${esc(config.login_visual_subtitle)}</p></div>`;
    const formPanel=document.createElement("section"); formPanel.className="qorg-login-form-panel";
    const top=document.createElement("div"); top.className="qorg-login-form-top"; mountLanguage(config,top); formPanel.append(top);
    const parent=page.parentNode; parent.insertBefore(wrapper,page); wrapper.append(visual,formPanel); formPanel.append(page);
    const card=page.querySelector(".page-card, .page-card-body") || page;
    const existingTitle=page.querySelector(".page-card-head h4, .page-card-head .page-card-head-title, .login-content h4");
    if(existingTitle && config.login_form_title) existingTitle.textContent=config.login_form_title;
    const subtitle=document.createElement("p"); subtitle.className="qorg-login-form-subtitle"; subtitle.textContent=config.login_form_subtitle||"";
    const head=page.querySelector(".page-card-head"); if(head && subtitle.textContent) head.append(subtitle);
    if(config.login_footer_text){const footer=document.createElement("div");footer.className="qorg-login-footer-text";footer.textContent=config.login_footer_text;formPanel.append(footer)}
    standardSocialAndSignupRemain();
  }
  call("qorg.qorg.design_system.api.get_login_experience").then(apply).catch(error=>console.warn("Q Org login experience unavailable",error));
})();
