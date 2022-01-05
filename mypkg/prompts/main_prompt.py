from mypkg.db_settings import session
from prompt_toolkit.application import Application
from prompt_toolkit.layout import HSplit, VSplit, Layout
from prompt_toolkit.widgets import Label, TextArea
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from mypkg.prompts.components import generate_main_chunk_components, generate_screen_title_label, generate_chunk_with_diff_screen, generate_move_button, generate_other_chunk_components, ChunkState

def generate_main_screen(chunk_sets, cur_chunk_set_idx, related_chunks):
    #main chunks components
    chunk_set = chunk_sets[cur_chunk_set_idx]

    add_chunks, remove_chunks = chunk_set.add_chunks, chunk_set.remove_chunks
    diff_area, all_chunks, chunk_state_list, chunk_with_check_boxes = generate_main_chunk_components(add_chunks, remove_chunks)

    #related and pending chunks components
    related_diff_area, all_related_chunks, related_state_list, related_with_check_boxes = generate_other_chunk_components(related_chunks)
    
    # commit message input field
    commit_msg_input = TextArea(
        height=2,
        prompt="commit message:",
        text=chunk_set.message,
        style="class:commit-message",
        multiline=True,
        wrap_lines=False,
    )
    
    # exit button and process
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

    def assign_selected_chunks(chunks, states):
        index = 0
    
        for chunk in chunks:
            state = states[index]
            if state == ChunkState.ASSIGN:
                chunk.chunk_set_id = chunk_set.id
            index += 1
        session.commit()

    def common_exit_process():
        commit_staged_chunks()
        assign_selected_chunks(related_chunks, related_state_list)

    prev_chunk_kb, next_chunk_kb = KeyBindings(), KeyBindings()

    @prev_chunk_kb.add("c-m")
    def _(event):
        common_exit_process()
        event.app.exit(result=cur_chunk_set_idx - 1)

    @next_chunk_kb.add("c-m")
    def _(event):
        common_exit_process()
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
    
    prev_chunk_button = generate_move_button(prev_button_label, is_not_first, prev_chunk_kb, prev_chunk_button_style)
    next_chunk_button = generate_move_button(next_button_label, True, next_chunk_kb, next_chunk_button_style)
    
    root_container = HSplit(
        [
            Label(text="Press `Enter` to show diff, press 'a' to include the chunk to this chunk set, press 'd' to put on pending status,\npress 'p' to move the chunk to previous chunk set, and press 'n' to move the chunk to next chunk set."),
            generate_screen_title_label("Suggested Chunk Sets({} chunks) (Page: {} / {})".format(len(all_chunks), cur_chunk_set_idx + 1, len(chunk_sets)), "class:page-num"),
            generate_chunk_with_diff_screen(chunk_with_check_boxes, diff_area),
            generate_screen_title_label("Related Chunks({} chunks)".format(len(related_chunks)), "class:related-label"),
            generate_chunk_with_diff_screen(related_with_check_boxes, related_diff_area),
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
            ("chunk-set-label", "bg:#4F7DA7 #000000"),
            ("check-box-label", "bg:#163360 #000000"),
            ("diff", "bg:#000000 #006600"),
            ("commit-message", "bg:#001177 #ffffff"),
            ("prev-chunk-button-first", "bg:#b22222 #454545"),
            ("prev-chunk-button-normal", "bg:#b22222 #ffffff"),
            ("next-chunk-button-last", "bg:#00bfff #ffff00 bold"),
            ("next-chunk-button-normal", "bg:#00bfff #ffffff"),
            ("page-num", "bg:#ffbf7f #000000"),
            ("related-label", "bg:#6395ed #000000"),
            ("pending-label", "bg:#2e8b57 #000000"),
            ("target-add-line", "bg:#043F04 #ffffff"),
            ("target-remove-line", "bg:#880000 #ffffff"),
            ("other-add-line", "bg:#7C9F7C #ffffff"),
            ("other-remove-line", "bg:#C98F8F #ffffff"),
            ("label-back", "bg:#C4C4C4 #ffffff"),
            ("patch-label", "bg:#454545 #ffffff"),
        ]
    )
    
    # define key bindings
    gen_kb = KeyBindings()
    gen_kb.add("down")(focus_next)
    gen_kb.add("up")(focus_previous)

    @gen_kb.add("c-q")
    def _(event):
        event.app.exit()

    @gen_kb.add("c-t")
    def _(event):
        event.app.layout.focus(commit_msg_input)

    @gen_kb.add("c-a")
    def _(event):
        if all_chunks:
            event.app.layout.focus(all_chunks[0])

    @gen_kb.add("c-b")
    def _(event):
        event.app.layout.focus(diff_area)

    @gen_kb.add("c-c")
    def _(event):
        if all_related_chunks:
            event.app.layout.focus(all_related_chunks[0])

    @gen_kb.add("c-d")
    def _(event):
        event.app.layout.focus(related_diff_area)

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

