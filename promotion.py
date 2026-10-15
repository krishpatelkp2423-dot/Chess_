import pygame
from board import BOARD_WIDTH, HEIGHT


def prompt_promotion(screen, color):
    """Show a modal dialog asking which piece to promote to.

    Returns the single-letter piece code ('q','r','b','n','k') in the
    correct case for the given color ('white' or 'black'). This function
    blocks until the user clicks a choice.
    """
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("DejaVuSans.ttf", 28)
    small = pygame.font.SysFont("DejaVuSans.ttf", 20)

    # choices (code, label)
    choices = [
        ("q", "Queen"),
        ("r", "Rook"),
        ("b", "Bishop"),
        ("n", "Knight"),
        ("k", "King"),
    ]

    # modal size and position (centered over the board area)
    modal_w = 400
    modal_h = 120
    modal_x = (BOARD_WIDTH - modal_w) // 2
    modal_y = (HEIGHT - modal_h) // 2

    # compute button rects
    btn_w = 70
    btn_h = 40
    gap = 10
    total_w = len(choices) * btn_w + (len(choices) - 1) * gap
    start_x = modal_x + (modal_w - total_w) // 2
    btns = []
    for i, (code, label) in enumerate(choices):
        x = start_x + i * (btn_w + gap)
        y = modal_y + 50
        btns.append((pygame.Rect(x, y, btn_w, btn_h), code, label))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                for rect, code, label in btns:
                    if rect.collidepoint(pos):
                        return code.upper() if color == "white" else code.lower()

        # draw translucent backdrop over board area
        overlay = pygame.Surface((BOARD_WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        # modal background
        pygame.draw.rect(screen, (240, 240, 240), (modal_x, modal_y, modal_w, modal_h))
        pygame.draw.rect(screen, (0, 0, 0), (modal_x, modal_y, modal_w, modal_h), 2)

        title = font.render("Choose promotion:", True, (10, 10, 10))
        screen.blit(title, (modal_x + 10, modal_y + 10))

        # draw buttons
        for rect, code, label in btns:
            pygame.draw.rect(screen, (200, 200, 200), rect)
            pygame.draw.rect(screen, (0, 0, 0), rect, 1)
            txt = small.render(label, True, (0, 0, 0))
            txt_rect = txt.get_rect(center=rect.center)
            screen.blit(txt, txt_rect)

        pygame.display.flip()
        clock.tick(30)
