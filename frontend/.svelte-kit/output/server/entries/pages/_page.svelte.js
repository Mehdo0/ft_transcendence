import { a2 as ensure_array_like, a as attr, a3 as attr_style, e as escape_html, a4 as stringify } from "../../chunks/renderer.js";
import "clsx";
function Canvas($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    $$renderer2.push(`<canvas class="svelte-dfb6jk"></canvas> `);
    {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]-->`);
  });
}
function _page($$renderer) {
  const colors = [
    "red",
    "orange",
    "yellow",
    "green",
    "blue",
    "indigo",
    "violet",
    "white",
    "black"
  ];
  let selected = colors[0];
  let size = 10;
  $$renderer.push(`<div class="container svelte-1uha8ag">`);
  Canvas($$renderer);
  $$renderer.push(`<!----> `);
  {
    $$renderer.push("<!--[0-->");
    $$renderer.push(`<div role="presentation" class="modal-background svelte-1uha8ag"><div class="menu svelte-1uha8ag"><div class="colors svelte-1uha8ag"><!--[-->`);
    const each_array = ensure_array_like(colors);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let color = each_array[$$index];
      $$renderer.push(`<button class="color svelte-1uha8ag"${attr("aria-label", color)}${attr("aria-current", selected === color)}${attr_style(`--color: ${stringify(color)}`)}></button>`);
    }
    $$renderer.push(`<!--]--></div> <label class="svelte-1uha8ag">small <input type="range"${attr("value", size)} min="1" max="50" class="svelte-1uha8ag"/> large</label></div></div>`);
  }
  $$renderer.push(`<!--]--> <div class="controls svelte-1uha8ag"><button class="show-menu svelte-1uha8ag">${escape_html("close")}</button></div></div>`);
}
export {
  _page as default
};
