from prompt_toolkit.application import Application
from prompt_toolkit.layout import HSplit, VSplit, Layout, Window, FormattedTextControl, BufferControl
from prompt_toolkit.application.current import get_app
from prompt_toolkit.widgets import Box, Button, Frame, Label, TextArea
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document

def chunk_selected(text_area, content):
    text_area.text = content

def exit_clicked():
    get_app().exit()

def generate_buffer_key_bindings(text_area, patch, check_box):
    kb = KeyBindings()
    
    @kb.add("c-m")
    def _(event):
        text_area.text = patch
    
    @kb.add("a")
    def _(event):
        check_box.text = " [*]"
    
    @kb.add("d")
    def _(event):
        check_box.text = " [ ]"
    
    return kb

def generate_buffer_window(buffer_text, text_area, patch, style, check_box):
    window = Window(
        BufferControl(
            Buffer(
                document=Document(buffer_text),
                read_only=True
            ),
            focusable=True,
            key_bindings=generate_buffer_key_bindings(text_area, patch, check_box),
        ),
        height=2,
        style=style,
        width=D(weight=2),
    )

    return window

def generate_chunk_buffers(add_chunks, remove_chunks, text_area, check_boxes):
    buffers = []
    index = 0
    for add_chunk in add_chunks:
        buffer_text = '{} \n({}, {})'.format(add_chunk.context.path, add_chunk.start_id, add_chunk.end_id)
        buffers.append(generate_buffer_window(buffer_text, text_area, add_chunk.generate_add_patch(), "class:add-chunk", check_boxes[index]))
        index += 1
    for remove_chunk in remove_chunks:
        buffer_text = '{} \n({}, {})'.format(remove_chunk.context.path, remove_chunk.start_id, remove_chunk.end_id)
        buffers.append(generate_buffer_window(buffer_text, text_area, remove_chunk.generate_remove_patch(), "class:remove-chunk", check_boxes[index]))
        index += 1
        
    return buffers

def generate_key_bindings():
    kb = KeyBindings()
    kb.add("down")(focus_next)
    kb.add("up")(focus_previous)
    return kb

def generate_label(text, style, width):
    window = Window(
        FormattedTextControl(text=text),
        height=1,
        width=width,
        style=style,
    )
    return window

def generate_chunks_with_check_box(check_boxes, all_chunks):
    check_box_contents = [Box(body=check_box, style="class:check-box", width=7) for check_box in check_boxes]
    return [VSplit([check_box_contents[i], all_chunks[i]]) for i in range(len(all_chunks))]

def generate_chunk_select_prompt(add_chunks, remove_chunks):
    text_area = FormattedTextControl()
    text_window = Window(text_area, z_index=0)
    exit_button = Button("Next Chunks", handler=exit_clicked)
    check_boxes = [Label(text=" [*]") for i in range(len(add_chunks) + len(remove_chunks))]
    all_chunks = generate_chunk_buffers(add_chunks, remove_chunks, text_area, check_boxes)
    chunk_with_check_boxes = generate_chunks_with_check_box(check_boxes, all_chunks)
    
    check_box_label = generate_label("State", "class:check-box-label", 7)
    chunk_set_label = generate_label("Chunk Sets", "class:chunk-set-label", D(weight=1))
    chunk_with_check_boxes.insert(0, VSplit([check_box_label, chunk_set_label]))
    input_field = TextArea(
        height=2,
        prompt="commit message:",
        style="class:commit-message",
        multiline=True,
        wrap_lines=False,
    )
    
    root_container = HSplit(
        [
            Label(text="Press `Enter` to show diff, and press 'space' to stage this chunk."),
            VSplit(
                [
                    HSplit(
                        [
                            HSplit(
                                chunk_with_check_boxes,
                                padding=0,
                            ),
                        ],
                        width=D(max=30, weight=1),
                        style="class:left-pane"
                    ),
                    HSplit(
                        [
                            Label(text="Diff", style="class:diff"),
                            Box(
                                body=Frame(text_window),
                                padding=0,
                                style='class:right-pane',
                            ),
                        ],
                        width=D(weight=3),
                    ),
                ],
                height=D(),
            ),
            input_field,
            exit_button,
        ]
    )

    style = Style(
        [
            ("left-pane", "bg:#454545 #ffffff"),
            ("right-pane", "bg:#000000 #ffffff"),
            ("add-chunk", "bg:#006600 #ffffff"),
            ("remove-chunk", "bg:#880000 #ffffff"),
            ("chunk-sets", "bg:#454545 #ffffff"),
            ("check-box", "bg:#151515 #ffffff"),
            ("chunk-set-label", "bg:#C6B1B1 #000000"),
            ("check-box-label", "bg:#D8EAEA #000000"),
            ("diff", "bg:#000000 #006600"),
            ("commit-message", "bg:#001177 #ffffff"),
            ("buffer focused", "bg:#ffffff"),
        ]
    )
    
    layout = Layout(container=root_container, focused_element=exit_button)
    application = Application(layout=layout, key_bindings=generate_key_bindings(), style=style, full_screen=True, mouse_support=True)
    return application

