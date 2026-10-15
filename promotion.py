import pygame
from board import BOARD_WIDTH, HEIGHT, PIECE_NAMES, get_font, get_piece_image


def prompt_promotion(screen, color):
    """Show a dialog asking which piece a pawn should become.

    Returns the piece letter ('q', 'r', 'b' or 'n') in the correct case for
    `color` ('white' or 'black'). Waits until the player clicks a choice.
    """
    clock = pygame.time.Clock()
    title_font = get_font(26)
    small = get_font(16)

    choices = ["q", "r", "b", "n"]

    # dialog size and position (centered over the board area)
    btn_size = 90
    gap = 14
    modal_w = len(choices) * btn_size + (len(choices) + 1) * gap
    modal_h = 190
    modal_x = (BOARD_WIDTH - modal_w) // 2
    modal_y = (HEIGHT - modal_h) // 2

    btns = []
    for i, code in enumerate(choices):
        x = modal_x + gap + i * (btn_size + gap)
        y = modal_y + 56
        btns.append((pygame.Rect(x, y, btn_size, btn_size), code))

    # Take a picture of the board once and draw the dialog over it each frame.
    # (Drawing the dark overlay straight onto the screen every frame would
    # keep making it darker until it turned black.)
    background = screen.copy()
    overlay = pygame.Surface((BOARD_WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    background.blit(overlay, (0, 0))

    while True:
        mouse = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, code in btns:
                    if rect.collidepoint(event.pos):
                        return code.upper() if color == "white" else code.lower()
            if event.type == pygame.KEYDOWN:
                # keyboard shortcuts: Q, R, B, N
                key = pygame.key.name(event.key)
                if key in choices:
                    return key.upper() if color == "white" else key.lower()

        screen.blit(background, (0, 0))

        # dialog background
        pygame.draw.rect(screen, (245, 245, 245), (modal_x, modal_y, modal_w, modal_h), border_radius=10)
        pygame.draw.rect(screen, (40, 40, 40), (modal_x, modal_y, modal_w, modal_h), 2, border_radius=10)

        title = title_font.render("Promote pawn to:", True, (10, 10, 10))
        screen.blit(title, title.get_rect(midtop=(modal_x + modal_w // 2, modal_y + 14)))

        for rect, code in btns:
            hovered = rect.collidepoint(mouse)
            pygame.draw.rect(screen, (200, 225, 200) if hovered else (220, 220, 220), rect, border_radius=8)
            pygame.draw.rect(screen, (90, 90, 90), rect, 1, border_radius=8)
            piece = code.upper() if color == "white" else code
            screen.blit(get_piece_image(piece, btn_size), rect.topleft)
            label = small.render(PIECE_NAMES[code], True, (40, 40, 40))
            screen.blit(label, label.get_rect(midtop=(rect.centerx, rect.bottom + 4)))

        pygame.display.flip()
        clock.tick(30)
