if(!customElements.get("quick-add-drawer")){class QuickAddDrawer extends SideDrawer{constructor(){super(),this.content=this.querySelector(".js-product-details"),this.footer=this.querySelector(".drawer__footer"),this.form=this.querySelector("product-form"),this.notification=this.querySelector(".js-added-to-cart"),this.backBtn=this.querySelector(".drawer__back-btn"),this.openCartDrawerLinks=this.querySelectorAll(".js-open-cart-drawer"),this.cartDrawer=document.querySelector("cart-drawer"),this.fetch=null,this.fetchedUrls=[],this.quickAddButtonMouseEnterHandler=this.handleQuickAddButtonMouseEnter.bind(this),this.documentClickHandler=this.handleDocumentClick.bind(this),document.addEventListener("click",this.documentClickHandler),this.addEventListener("on:variant:change",this.handleVariantChange.bind(this)),this.openCartDrawerLinks.forEach(link=>{link.addEventListener("click",this.handleOpenCartClick.bind(this))}),theme.device.hasHover&&theme.mediaMatches.md&&(document.querySelectorAll(".js-quick-add").forEach(button=>{this.bindQuickAddButtonMouseEnter(button)}),"MutationObserver"in window&&(this.observer=new MutationObserver(mutations=>{mutations.forEach(mutation=>{mutation.addedNodes.forEach(node=>{node.nodeType===Node.ELEMENT_NODE&&node.querySelectorAll(".js-quick-add").forEach(button=>{this.bindQuickAddButtonMouseEnter(button)})}),mutation.removedNodes.forEach(node=>{node.nodeType===Node.ELEMENT_NODE&&node.querySelectorAll(".js-quick-add").forEach(button=>{button.removeEventListener("mouseenter",this.quickAddButtonMouseEnterHandler)})})})}),this.observer.observe(document.body,{childList:!0,subtree:!0})))}disconnectedCallback(){document.removeEventListener("click",this.documentClickHandler),document.querySelectorAll(".js-quick-add").forEach(button=>{button.removeEventListener("mouseenter",this.quickAddButtonMouseEnterHandler)}),this.observer&&this.observer.disconnect()}bindQuickAddButtonMouseEnter(button){button.dataset.quickAddListenerAdded||(button.dataset.quickAddListenerAdded="true",button.addEventListener("mouseenter",this.quickAddButtonMouseEnterHandler))}handleQuickAddButtonMouseEnter(evt){this.fetchedUrls.includes(evt.target.dataset.productUrl)||(this.fetch={url:evt.target.dataset.productUrl,promise:fetch(evt.target.dataset.productUrl)},this.fetchedUrls.push(evt.target.dataset.productUrl))}handleOpenCartClick(evt){this.cartDrawer?(evt.preventDefault(),this.cartDrawer.open()):window.location.pathname===theme.routes.cart&&(evt.preventDefault(),this.close())}handleDocumentClick(evt){if(evt.target.matches(".js-quick-add"))if(this.cartDrawer&&this.cartDrawer.ariaHidden==="false"){const overlay=document.querySelector(".js-overlay.is-visible");overlay&&(overlay.style.transitionDelay="200ms"),this.cartDrawer.close(),setTimeout(()=>{this.backBtn.hidden=!1,this.open(evt.target),overlay&&(overlay.style.transitionDelay="")},200)}else this.open(evt.target)}handleVariantChange(evt){let url=this.productUrl;if(evt.detail.variant){const separator=this.productUrl.split("?").length>1?"&":"?";url+=`${separator}variant=${evt.detail.variant.id}`}this.querySelectorAll(".js-prod-link").forEach(link=>{link.href=url})}async open(opener){if(opener.setAttribute("aria-disabled","true"),this.notification&&(this.notification.hidden=!0),this.productUrl&&this.productUrl===opener.dataset.productUrl){super.open(opener),opener.removeAttribute("aria-disabled");return}this.productUrl=opener.dataset.productUrl,this.content.innerHTML="",this.classList.add("is-loading"),this.content.classList.add("drawer__content--out"),this.footer.classList.add("drawer__footer--out"),super.open(opener),(!this.fetch||this.fetch.url!==opener.dataset.productUrl)&&(this.fetch={url:opener.dataset.productUrl,promise:fetch(opener.dataset.productUrl)});const response=await this.fetch.promise;if(response.ok){const tmpl=document.createElement("template");tmpl.innerHTML=await response.text(),this.productEl=tmpl.content.querySelector(".cc-main-product .js-product"),this.renderProduct(opener)}this.fetch=null,opener.removeAttribute("aria-disabled")}close(){super.close(()=>{this.backBtn.hidden=!0})}renderProduct(opener){const sectionId=this.productEl.dataset.section;this.productEl.innerHTML=this.productEl.innerHTML.replaceAll(sectionId,"quickadd");const variantPicker=this.productEl.querySelector("variant-picker");variantPicker&&(variantPicker.dataset.updateUrl="false",this.selectFirstVariant=variantPicker.dataset.selectFirstVariant==="true");const sizeChartModal=this.productEl.querySelector('[data-modal="size-chart"]');sizeChartModal&&sizeChartModal.remove(),this.updateContent(),this.updateForm();const activeMedia=this.productEl.querySelector(".media-viewer__item.is-current-variant");activeMedia&&this.updateMedia(activeMedia.dataset.mediaId),opener.dataset.selectedColor&&this.selectFirstVariant&&setTimeout(this.setActiveVariant.bind(this,opener),10)}setActiveVariant(opener){if(this.querySelector(`.opt-btn[value="${opener.dataset.selectedColor}"]`))this.querySelector(`.opt-btn[value="${opener.dataset.selectedColor}"]`).click();else{const colorOptionDropdown=this.querySelector(`.custom-select__option[data-value="${opener.dataset.selectedColor}"]`);colorOptionDropdown&&colorOptionDropdown.closest("custom-select").selectOption(colorOptionDropdown)}}updateMedia(mediaId){const img=this.productEl.querySelector(`[data-media-id="${mediaId}"] img`);if(!img)return;const src=img.src?img.src.split("&width=")[0]:img.dataset.src.split("&width=")[0],container=this.querySelector(".quick-add-info__media"),width=container.offsetWidth,aspectRatio=img.width/img.height;container.innerHTML=`
        <img src="${src}&width=${width}" srcset="${src}&width=${width}, ${src}&width=${width*2} 2x" width="${width*2}" height="${width*2/aspectRatio}" alt="${img.alt}">
      `}updateContent(){let weightElem=this.getElementHtml(".product-info__weight");weightElem&&weightElem.length>0&&(weightElem=`<div class="product-info__weight text-sm mt-2">${weightElem}</div>`),this.content.innerHTML=`
        <div class="quick-add-info grid mb-8">
          <div class="quick-add-info__media${theme.settings.blendProductImages?" image-blend":""}"></div>
          <div class="quick-add-info__details">
            <div class="product-vendor-sku mb-2 text-sm">
              ${this.getElementHtml(".product-vendor-sku")}
            </div>
            <div class="product-title">
              <a class="h6 js-prod-link" href="${this.productUrl}">
                ${this.getElementHtml(".product-title")}
              </a>
            </div>
            ${weightElem}
            <hr>
            <div class="product-price">
              ${this.getElementHtml(".product-price")}
            </div>
            <div class="text-theme-light text-sm mt-4">
              <a href="${this.productUrl}" class="link js-prod-link">
                ${theme.strings.viewDetails}
              </a>
            </div>
          </div>
          <div class="quick-add-info__details md:hidden"></div>
        </div>
        <div class="product-options">
          ${this.getElementHtml(".product-options",".custom-option:not(.quick-add-hidden)")}
        </div>
        <div class="product-backorder">
          ${this.getElementHtml(".product-backorder")}
        </div>
      `,this.classList.remove("is-loading"),this.content.classList.remove("drawer__content--out")}updateForm(){const productForm=this.productEl.querySelector("product-form");if(this.footer.classList.remove("quick-add__footer-message"),productForm)this.form.innerHTML=productForm.innerHTML,this.form.init(),Shopify&&Shopify.PaymentButton&&Shopify.PaymentButton.init();else{const signUpForm=this.productEl.querySelector(".product-signup");signUpForm?this.form.innerHTML=signUpForm.innerHTML:(this.footer.classList.add("quick-add__footer-message"),this.form.innerHTML=`
            <div class="alert quick-add__alert bg-info-bg text-info-text">
              <div class="flex">
                <div>
                  <svg class="icon icon--price_tag" width="32" height="32" viewBox="0 0 16 16" aria-hidden="true" focusable="false" role="presentation">
                    <path fill="currentColor" d="M7.59 1.34a1 1 0 01.7-.29h5.66a1 1 0 011 1v5.66a1 1 0 01-.3.7L7.6 15.5a1 1 0 01-1.42 0L.52 9.83a1 1 0 010-1.42l7.07-7.07zm6.36 6.37l-7.07 7.07-5.66-5.66L8.3 2.05h5.66v5.66z" fill-rule="evenodd"/>
                    <path fill="currentColor" d="M9.7 6.3a1 1 0 101.42-1.42 1 1 0 00-1.41 1.41zM9 7a2 2 0 102.83-2.83A2 2 0 009 7z" fill-rule="evenodd"/>
                  </svg>
                </div>
                <div>
                  <p class="text-h6 font-bold mb-2">${theme.strings.awaitingSale}</p>
                  <a class="link js-prod-link" href="${this.productUrl}">${theme.strings.viewDetails}</a>
                </div>
              </div>
            </div>`)}this.footer.classList.remove("drawer__footer--out")}getElementHtml(selector,...additionalSelectors){const selectors=[selector].concat(additionalSelectors);let html="";return selectors.forEach(sel=>{const els=this.productEl.querySelectorAll(sel);Array.from(els).forEach(el=>{html+=el.innerHTML})}),html}addedToCart(){this.notification&&(setTimeout(()=>{this.notification.hidden=!1},300),setTimeout(()=>{this.notification.hidden=!0},this.notification.dataset.visibleFor))}}customElements.define("quick-add-drawer",QuickAddDrawer)}
//# sourceMappingURL=/cdn/shop/t/19/assets/quick-add.js.map?v=36670813702257243391789000854
