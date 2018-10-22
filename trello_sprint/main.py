import argparse
import configparser
import sys

from trello import TrelloClient
from trello.member import Member


def get_client():
    config = configparser.ConfigParser()
    config_path = 'auth.conf'

    if not config.read(config_path):
        print('Could not read %s' % config_path)
        sys.exit(1)

    if not config.has_section('trello'):
        click.echo('Config file does not contain section [trello].')
        sys.exit(1)

    return TrelloClient(
        api_key=config['trello']['api_key'],
        api_secret=config['trello']['api_secret'],
        token=config['trello']['token'],
    )


client = get_client()


def get_cli_options():
    parser = argparse.ArgumentParser(description='Generate a report per (board, sprint)')
    parser.add_argument('--board', help='board name', required=True)
    parser.add_argument('--sprint', type=int, help='integer', required=True)

    args = parser.parse_args()
    return args


def get_board(name):
    boards = client.list_boards('open')
    for b in boards:
        if b.name == name:
            return b


def get_list(lists, name):
    name = name.lower()

    for l in lists:
        if l.name.lower() == name:
            return l


def get_label(board, name):
    name = name.lower()
    labels = board.get_labels()
    for l in labels:
        if l.name.lower() == name:
            return l


def get_sprint_cards(trello_list, sprint):
    cards = trello_list.list_cards()
    sprint = 'sprint %s' % sprint

    sprint_cards = []
    for c in cards:
        labels = c.labels
        for l in labels or []:
            if l.name.lower() == sprint:
                sprint_cards.append(c)
                break
    return sprint_cards


def report_cards(cards):
    if not cards:
        return

    print(cards[0].trello_list.name)
    for c in cards:
        member_names = []
        if c.member_id:
            for m_id in c.member_id:
                member = Member(client, m_id)
                member.fetch()
                member_names.append(member.full_name)

        fields = c.custom_fields
        hours = None
        for f in fields:
            if f.name == 'Hours':
                hours = f.value
        row = '  %s' % c.name
        if member_names:
            row += ', %s' % ', '.join(member_names)
        if hours:
            row += ', %s hours' % hours
        print(row)
    print()


def main():
    cli_options = get_cli_options()
    board = get_board(cli_options.board)
    if not board:
        print('Board %s not found' % cli_options.board)
        return

    lists = board.list_lists('open')

    report_cards(get_sprint_cards(
        get_list(lists, 'Backlog'), cli_options.sprint))
    report_cards(get_sprint_cards(
        get_list(lists, 'Doing'), cli_options.sprint))
    report_cards(get_sprint_cards(
        get_list(lists, 'Done'), cli_options.sprint))


if __name__ == '__main__':
    main()
