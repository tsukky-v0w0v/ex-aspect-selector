import os
import gradio as gr

from modules import scripts, ui, ui_components

base_dir = scripts.basedir()
PRESETS_FILE = os.path.join(base_dir, "aspect_presets.txt")
RESOLUTIONS_FILE = os.path.join(base_dir, "base_resolutions.txt")


def log(text):
    print(f"[aspect selector] {text}")


class ExAspectSelectorScript(scripts.Script):
    component_map = {}

    aspect_presets = []
    base_resolutions = []
    all_resolutions = {}

    def __init__(self):
        super().__init__()
        self.component_map = {"width": None, "height": None}
        self.load_aspect_presets()
        self.load_base_resolutions()
        self.calc_all_resolutions()


    def title(self):
        return "Ex Aspect Selector"
    

    def show(self, is_img2img):
        return scripts.AlwaysVisible
    

    def after_component(self, component, **kwargs):
        id_prefix = "txt2img" if self.is_txt2img else "img2img"

        # width, heightコンポーネントを取得
        if component.elem_id == f"{id_prefix}_width": self.component_map["width"] = component
        if component.elem_id == f"{id_prefix}_height": self.component_map["height"] = component

        # UIの作成
        # output_panelの下に作成
        if component.elem_id == f"{id_prefix}_generation_info_button":
            with gr.Row(variant="compact", equal_height=True):
                preset = gr.Dropdown(
                    label="aspect selector preset", 
                    show_label=True, 
                    choices=self.aspect_presets, 
                    value=self.aspect_presets[0], 
                    scale=4, 
                    elem_id=f"{id_prefix}_resolution_selector_preset"
                )
                base_resolution = gr.Dropdown(
                    label="base resolution", 
                    show_label=True, 
                    choices=self.base_resolutions, 
                    value=self.base_resolutions[0], 
                    scale=1, 
                    elem_id=f"{id_prefix}_resolution_selector_base_resolution"
                )
                refresh_button = ui_components.ToolButton(
                    value=ui.refresh_symbol, 
                    elem_id=f"{id_prefix}_resolution_selector_refresh_button"
                )

            # assign event listener
            refresh_button.click(fn=self.on_refresh_button_clicked, outputs=[preset, base_resolution])
            preset.change(fn=self.apply_resolution, inputs=[preset, base_resolution], outputs=[self.component_map["width"], self.component_map["height"]], show_progress=False)
            base_resolution.change(fn=self.apply_resolution, inputs=[preset, base_resolution], outputs=[self.component_map["width"], self.component_map["height"]], show_progress=False)
    

    def load_aspect_presets(self):
        try:
            with open(PRESETS_FILE, mode="r", encoding="utf-8") as file:
                lines = [line.strip() for line in file.readlines()]
        except:
            lines = ["1:1"]
        
        self.aspect_presets = ["None"] + lines
    

    def load_base_resolutions(self):
        try:
            with open(RESOLUTIONS_FILE, mode="r", encoding="utf-8") as file:
                lines = [line.strip() for line in file.readlines()]
        except:
            lines = [1024]
        
        self.base_resolutions = lines
    
    
    def calc_all_resolutions(self):
        for base in self.base_resolutions:
            resolutions = {}
            
            for aspect in self.aspect_presets:
                try:
                    a, b = aspect.split(":")
                    a, b = int(a), int(b)
                    base = int(base)

                    w, h = self.calc_resolution(a, b, base)
                except:
                    w = h = None
                
                resolutions[str(aspect)] = (w, h)
            
            self.all_resolutions[str(base)] = resolutions
        
    
    def calc_resolution(self, a: int, b: int, base: int):
        target_area = base ** 2

        closest_diff = float("inf")
        best_w = best_h = None

        for x in range(64, int(base * 2), 64):
            y = int((x * b) / a)

            y = (y + 63) // 64 * 64

            area = x * y
            if area > target_area:
                continue

            diff = target_area - area
            # diff = abs(target_area - area)

            if diff < closest_diff:
                closest_diff = diff
                best_w, best_h = x, y
        
        return best_w, best_h


    def apply_resolution(self, aspect, base):
        resolutions = self.all_resolutions.get(str(base), {})
        w, h = resolutions.get(str(aspect), (None, None))

        if w and h:
            log(f"Selected aspect: {aspect} -> resolution: {(w, h)}")
            return w, h
        else:
            return gr.update(), gr.update()
        
    
    def on_refresh_button_clicked(self):
        self.load_aspect_presets()
        self.load_base_resolutions()
        self.calc_all_resolutions()

        return gr.update(choices=self.aspect_presets), gr.update(choices=self.base_resolutions)



