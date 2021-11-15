from mypkg.db_settings import session
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
from functools import partial

CHECKBOXWIDTH = 7

def chunk_selected(text_area, content):
    text_area.text = content

def generate_buffer_key_bindings(text_area, patch, check_box, chunk_state_list, index):
    kb = KeyBindings()
    
    @kb.add("c-m")
    def _(event):
        text_area.text = patch
    
    @kb.add("a")
    def _(event):
        check_box.text = " [*]"
        chunk_state_list[index] = True
    
    @kb.add("d")
    def _(event):
        check_box.text = " [ ]"
        chunk_state_list[index] = False
    
    return kb

def generate_buffer_window(buffer_text, text_area, patch, style, check_box, chunk_state_list, index):
    window = Window(
        BufferControl(
            Buffer(
                document=Document(buffer_text),
                read_only=True
            ),
            focusable=True,
            key_bindings=generate_buffer_key_bindings(text_area, patch, check_box, chunk_state_list, index),
        ),
        height=2,
        style=style,
        width=D(weight=2),
    )

    return window

def generate_chunk_buffers(add_chunks, remove_chunks, text_area, check_boxes, chunk_state_list):
    buffers = []
    index = 0
    for add_chunk in add_chunks:
        buffer_text = '{} \n({}, {})'.format(add_chunk.context.path, add_chunk.start_id, add_chunk.end_id)
        buffers.append(generate_buffer_window(buffer_text, text_area, add_chunk.generate_add_patch(), "class:add-chunk", check_boxes[index], chunk_state_list, index))
        index += 1
    for remove_chunk in remove_chunks:
        buffer_text = '{} \n({}, {})'.format(remove_chunk.context.path, remove_chunk.start_id, remove_chunk.end_id)
        buffers.append(generate_buffer_window(buffer_text, text_area, remove_chunk.generate_remove_patch(), "class:remove-chunk", check_boxes[index], chunk_state_list, index))
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
    check_box_contents = [Box(body=check_box, style="class:check-box", width=CHECKBOXWIDTH) for check_box in check_boxes]
    return [VSplit([check_box_contents[i], all_chunks[i]]) for i in range(len(all_chunks))]

def generate_chunk_select_prompt(chunk_set, chunk_set_id):
    add_chunks, remove_chunks = chunk_set.add_chunks, chunk_set.remove_chunks
    text_area = FormattedTextControl()
    text_window = Window(text_area, z_index=0)
    
    check_boxes = [Label(text=" [*]") for i in range(len(add_chunks) + len(remove_chunks))]
    chunk_state_list = [True for i in range(len(add_chunks) + len(remove_chunks))]
    all_chunks = generate_chunk_buffers(add_chunks, remove_chunks, text_area, check_boxes, chunk_state_list)
    chunk_with_check_boxes = generate_chunks_with_check_box(check_boxes, all_chunks)
    
    check_box_label = generate_label("State", "class:check-box-label", CHECKBOXWIDTH)
    chunk_set_label = generate_label("Chunk Sets", "class:chunk-set-label", D(weight=1))
    chunk_with_check_boxes.insert(0, VSplit([check_box_label, chunk_set_label]))
    commit_msg_input = TextArea(
        height=2,
        prompt="commit message:",
        style="class:commit-message",
        multiline=True,
        wrap_lines=False,
    )

    def exit_clicked():
        chunk_set.message = commit_msg_input.text
        session.commit()
        index = 0
        for add_chunk in add_chunks:
            if not chunk_state_list[index]:
                add_chunk.chunk_set_id = chunk_set_id
            index += 1
        session.commit()
        for remove_chunk in remove_chunks:
            if not chunk_state_list[index]:
                remove_chunk.chunk_set_id = chunk_set_id
            index += 1
        session.commit()
 
        get_app().exit()
    
    exit_button = Button("Next Chunks", handler=exit_clicked)
    
    root_container = HSplit(
        [
            Label(text="Press `Enter` to show diff, press 'a' to stage the chunk, and press 'd' to unstage."),
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
            commit_msg_input,
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

