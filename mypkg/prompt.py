from mypkg.db_settings import session
from prompt_toolkit.application import Application
from prompt_toolkit.layout import HSplit, VSplit, Layout, Window, FormattedTextControl, BufferControl, DummyControl, ScrollablePane
from prompt_toolkit.application.current import get_app
from prompt_toolkit.widgets import Box, Button, Frame, Label, TextArea
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from functools import partial
from mypkg.models.add_chunk import AddChunk
from mypkg.models.remove_chunk import RemoveChunk
from enum import Enum, auto

class ChunkState(Enum):
    KEEP = auto()
    NEXT = auto()
    PREV = auto()
    PENDING = auto()
    ASSIGN = auto()

CHECKBOXWIDTH = 7

def chunk_selected(text_area, content):
    text_area.text = content

# chunk contents generators
def generate_buffer_key_bindings(text_area, patch, check_box, chunk_state_list, index):
    kb = KeyBindings()
    
    @kb.add("c-m")
    def _(event):
        text_area.text = patch
    
    @kb.add("a")
    def _(event):
        check_box.text = " [*]"
        chunk_state_list[index] = ChunkState.KEEP
    
    @kb.add("d")
    def _(event):
        check_box.text = " [x]"
        chunk_state_list[index] = ChunkState.PENDING

    @kb.add("p")
    def _(event):
        check_box.text = " [p]"
        chunk_state_list[index] = ChunkState.PREV

    @kb.add("n")
    def _(event):
        check_box.text = " [n]"
        chunk_state_list[index] = ChunkState.NEXT
    
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

def generate_chunks_with_check_box(check_boxes, all_chunks):
    check_box_contents = [Box(body=check_box, style="class:check-box", width=CHECKBOXWIDTH) for check_box in check_boxes]
    return [VSplit([check_box_contents[i], all_chunks[i]]) for i in range(len(all_chunks))]

# general content generators
def generate_label(text, style, width):
    window = Window(
        FormattedTextControl(text=text),
        height=1,
        width=width,
        style=style,
    )
    return window

# candidate contents generators
def generate_candidate_key_bindings(text_area, patch, check_box, candidate_state_list, index):
    kb = KeyBindings()
    
    @kb.add("c-m")
    def _(event):
        text_area.text = patch
    
    @kb.add("a")
    def _(event):
        check_box.text = " [*]"
        candidate_state_list[index] = ChunkState.ASSIGN
    
    @kb.add("d")
    def _(event):
        check_box.text = " [ ]"
        candidate_state_list[index] = ChunkState.KEEP
    
    return kb

def generate_candidate_window(buffer_text, text_area, patch, style, check_box, candidate_state_list, index):
    window = Window(
        BufferControl(
            Buffer(
                document=Document(buffer_text),
                read_only=True
            ),
            focusable=True,
            key_bindings=generate_candidate_key_bindings(text_area, patch, check_box, candidate_state_list, index),
        ),
        height=3,
        style=style,
        width=D(weight=2)
    )
    
    return window

def generate_candidate_buffers(candidates, text_area, check_boxes, candidate_state_list):
    buffers = []
    index = 0
    for candidate in candidates:
        buffer_text = '{} \n({}, {})\nPage: {}'.format(candidate.context.path, candidate.start_id, candidate.end_id, candidate.chunk_set_id)
        if isinstance(candidate, AddChunk):
            buffers.append(generate_candidate_window(buffer_text, text_area, candidate.generate_add_patch(), "class:add-chunk", check_boxes[index], candidate_state_list, index))
        else:
            buffers.append(generate_candidate_window(buffer_text, text_area, candidate.generate_remove_patch(), "class:remove-chunk", check_boxes[index], candidate_state_list, index))
        index += 1
    
    return buffers

def generate_chunk_with_diff_screen(chunk_with_check_boxes, diff_area):
    check_box_label = generate_label("State", "class:check-box-label", CHECKBOXWIDTH)
    chunk_set_label = generate_label("Chunk Sets", "class:chunk-set-label", D(weight=1))
    
    screen = VSplit(
        [
            HSplit(
                [
                    VSplit([check_box_label, chunk_set_label]),
                    ScrollablePane(
                        HSplit(
                            chunk_with_check_boxes,
                            width=D(max=30, weight=1),
                            style="class:left-pane"
                        )
                    )
                ]
            ),
            HSplit(
                [
                    Label(text="Diff", style="class:diff"),
                    Box(
                        body=Frame(ScrollablePane(diff_area)),
                        padding=0,
                        style='class:right-pane',
                    ),
                ],
                width=D(weight=3),
            ),
        ],
        height=D(),
    )
    
    return screen

def generate_screen_title_label(text, style):
    screen = VSplit(
        [
            Window(DummyControl()),
            Window(DummyControl()),
            Label(text=text, style=style),
            Window(DummyControl()),
            Window(DummyControl()),
        ]
    )
    
    return screen

def generate_chunk_select_prompt(chunk_sets, cur_chunk_set_idx, candidates, pending_chunks):
    chunk_set = chunk_sets[cur_chunk_set_idx]
    is_not_first = cur_chunk_set_idx > 0
    is_not_last = cur_chunk_set_idx < len(chunk_sets) - 1
    
    if is_not_first:
        prev_chunk = chunk_sets[cur_chunk_set_idx - 1]
    else:
        prev_chunk = None
        
    if is_not_last:
        next_chunk = chunk_sets[cur_chunk_set_idx + 1]
    else:
        next_chunk = None
    
    add_chunks, remove_chunks = chunk_set.add_chunks, chunk_set.remove_chunks
    diff_text = FormattedTextControl(focusable=True)
    diff_area = Window(diff_text)
    
    check_boxes = [Label(text=" [*]") for i in range(len(add_chunks) + len(remove_chunks))]
    chunk_state_list = [ChunkState.KEEP for i in range(len(add_chunks) + len(remove_chunks))]
    all_chunks = generate_chunk_buffers(add_chunks, remove_chunks, diff_text, check_boxes, chunk_state_list)
    chunk_with_check_boxes = generate_chunks_with_check_box(check_boxes, all_chunks)
    
    commit_msg_input = TextArea(
        height=2,
        prompt="commit message:",
        text=chunk_set.message,
        style="class:commit-message",
        multiline=True,
        wrap_lines=False,
    )
    
    def commit_staged_chunks():
        chunk_set.message = commit_msg_input.text
        session.commit()
        index = 0
        cur_chunks = []
        cur_chunks.extend(add_chunks)
        cur_chunks.extend(remove_chunks)

        for cur_chunk in cur_chunks:
            chunk_state = chunk_state_list[index]
            if chunk_state == ChunkState.PREV and prev_chunk:
                cur_chunk.chunk_set_id = prev_chunk.id
            elif chunk_state == ChunkState.NEXT and next_chunk:
                cur_chunk.chunk_set_id = next_chunk.id
            elif chunk_state == ChunkState.PENDING:
                cur_chunk.chunk_set_id = None
            index += 1
        session.commit()
        
    def assign_selected_candidates():
        index = 0
    
        for candidate in candidates:
            candidate_state = candidate_state_list[index]
            if candidate_state == ChunkState.ASSIGN:
                candidate.chunk_set_id = chunk_set.id
            index += 1
        session.commit()

    prev_chunk_kb, next_chunk_kb = KeyBindings(), KeyBindings()

    @prev_chunk_kb.add("c-m")
    def _(event):
        commit_staged_chunks()
        assign_selected_candidates()
        event.app.exit(result=cur_chunk_set_idx - 1)

    @next_chunk_kb.add("c-m")
    def _(event):
        commit_staged_chunks()
        assign_selected_candidates()
        event.app.exit(result=cur_chunk_set_idx + 1)

    if is_not_first:
        prev_chunk_button_style = "class:prev-chunk-button-normal"
        prev_button_label = "Prev Chunks"
    else:
        prev_chunk_button_style = "class:prev-chunk-button-first"
        prev_button_label = "Prev Chunks(This is the first chunks)"

    if is_not_last:
        next_chunk_button_style = "class:next-chunk-button-normal"
        next_button_label = "Next Chunks"
    else:
        next_chunk_button_style = "class:next-chunk-button-last"
        next_button_label = "Finish Split(This is the last chunks)"
    
    prev_chunk_button = Window(
        BufferControl(
            Buffer(
                document=Document(prev_button_label),
                read_only=True,
            ),
            focusable=is_not_first,
            key_bindings=prev_chunk_kb
        ),
        height=1,
        style=prev_chunk_button_style,
    )
    
    next_chunk_button = Window(
        BufferControl(
            Buffer(
                document=Document(next_button_label),
                read_only=True,
            ),
            focusable=True,
            key_bindings=next_chunk_kb
        ),
        height=1,
        style=next_chunk_button_style,
    )
    
    #candidate chunks components
    candidate_diff_text = FormattedTextControl(focusable=True)
    candidate_diff_area = Window(candidate_diff_text)
    
    candidate_check_boxes = [Label(text=" [ ]") for i in range(len(candidates))]
    candidate_state_list = [ChunkState.KEEP for i in range(len(candidates))]
    all_candidates = generate_candidate_buffers(candidates, candidate_diff_text, candidate_check_boxes, candidate_state_list)
    candidate_with_check_boxes = generate_chunks_with_check_box(candidate_check_boxes, all_candidates)

    #pending chunks components
    pending_diff_text = FormattedTextControl(focusable=True)
    pending_diff_area = Window(pending_diff_text)

    pending_check_boxes = [Label(text=" [ ]") for i in range(len(pending_chunks))]
    pending_state_list = [ChunkState.KEEP for i in range(len(pending_chunks))]
    all_pendings = generate_candidate_buffers(pending_chunks, pending_diff_text, pending_check_boxes, pending_state_list)
    pending_with_check_boxes = generate_chunks_with_check_box(pending_check_boxes, all_pendings)
    
    root_container = HSplit(
        [
            Label(text="Press `Enter` to show diff, press 'a' to stage the chunk, and press 'd' to unstage."),
            generate_screen_title_label("Suggested Chunk Sets({} chunks) (Page: {} / {})".format(len(all_chunks), cur_chunk_set_idx + 1, len(chunk_sets)), "class:page-num"),
            generate_chunk_with_diff_screen(chunk_with_check_boxes, diff_area),
            generate_screen_title_label("Candidate Chunks({} chunks)".format(len(candidates)), "class:candidates-label"),
            generate_chunk_with_diff_screen(candidate_with_check_boxes, candidate_diff_area),
            generate_screen_title_label("Pending Chunks({} chunks)".format(len(pending_chunks)), "class:pending-label"),
            generate_chunk_with_diff_screen(pending_with_check_boxes, pending_diff_area),
            commit_msg_input,
            VSplit(
                [
                    prev_chunk_button,
                    next_chunk_button,
                ]
            ),
        ]
    )

    # define styles
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
            ("prev-chunk-button-first", "bg:#b22222 #454545"),
            ("prev-chunk-button-normal", "bg:#b22222 #ffffff"),
            ("next-chunk-button-last", "bg:#00bfff #ffff00 bold"),
            ("next-chunk-button-normal", "bg:#00bfff #ffffff"),
            ("page-num", "bg:#ffbf7f #000000"),
            ("candidates-label", "bg:#6395ed #000000"),
            ("pending-label", "bg:#6395ed #000000"),
        ]
    )
    
    # define key bindings
    gen_kb = KeyBindings()
    gen_kb.add("down")(focus_next)
    gen_kb.add("up")(focus_previous)

    @gen_kb.add("c-c")
    @gen_kb.add("c-q")
    def _(event):
        event.app.exit()

    @gen_kb.add("c-t")
    def _(event):
        event.app.layout.focus(commit_msg_input)

    @gen_kb.add("c-e")
    def _(event):
        event.app.layout.focus(all_chunks[0])

    @gen_kb.add("c-r")
    def _(event):
        event.app.layout.focus(all_candidates[0])

    @gen_kb.add("c-d")
    def _(event):
        event.app.layout.focus(diff_area)

    @gen_kb.add("c-f")
    def _(event):
        event.app.layout.focus(candidate_diff_area)

    @gen_kb.add("c-p")
    def _(event):
        if is_not_first:
            event.app.layout.focus(prev_chunk_button)

    @gen_kb.add("c-n")
    def _(event):
        event.app.layout.focus(next_chunk_button)
    
    # define layout and application
    layout = Layout(container=root_container, focused_element=next_chunk_button)
    application = Application(layout=layout, key_bindings=gen_kb, style=style, full_screen=True, mouse_support=True)
    return application

