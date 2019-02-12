#!/usr/bin/env python
import argparse
import configparser
import sys

from trello import TrelloClient
from trello.member import Member

CLIENT = None
# Keep members information
MEMBERS_CACHE = {}
LABEL_UNPLANNED = 'UNPLANNED'
FIELD_BUGZILLA = 'BUGZILLA'

_INCLUDE_MEMBERS = False


class ListNotFound(Exception):
    pass


def get_client(config_path):
    global CLIENT
    if CLIENT is None:
        config = configparser.ConfigParser()

        if not config.read(config_path):
            print('Could not read %s' % config_path)
            sys.exit(1)

        if not config.has_section('trello'):
            print('Config file does not contain section [trello].')
            sys.exit(1)

        CLIENT = TrelloClient(
            api_key=config['trello']['api_key'],
            api_secret=config['trello']['api_secret'],
            token=config['trello']['token'],
        )

    return CLIENT


def get_cli_options():
    global _INCLUDE_MEMBERS

    parser = argparse.ArgumentParser(
        description='Generate a report per (board, sprint)')
    parser.add_argument('board', help='Trello board name')
    parser.add_argument('--config', help='TODO', required=True)
    parser.add_argument('--include-members', action='store_true',
                        help='If set, include members to the report',
                        default=False)

    # TODO(lucasagomes): Create an option to fetch information from
    # Bugzilla when the link is available in the card. For example, to
    # determine whether it's a blocker or not (avoiding duplication to
    # have the information in both places, trello and bugzilla)

    args = parser.parse_args()

    _INCLUDE_MEMBERS = args.include_members

    return args


def get_board(name):
    boards = CLIENT.list_boards('open')
    for b in boards:
        if b.name == name:
            return b


def get_list(lists, name):
    name = name.lower()

    for l in lists:
        if l.name.lower() == name:
            return l
    else:
        raise ListNotFound('List named "%s" was not found' % name)


def list_members_from_card(card):
    members = []
    if not _INCLUDE_MEMBERS or not card.member_id:
        return members

    for mid in card.member_id:
        if mid not in MEMBERS_CACHE:
            member = Member(CLIENT, mid)
            member.fetch()
            MEMBERS_CACHE[mid] = member.full_name
        members.append(MEMBERS_CACHE[mid])
    return members


def is_card_unplanned(card):
    for l in card.labels or []:
        if l.name.upper() == LABEL_UNPLANNED:
            return True
    return False


def parse_cards_from_list(lists, list_name):
    cards = {'planned': [], 'unplanned': []}
    tlist = get_list(lists, list_name)
    for c in tlist.list_cards():
        card = {}
        card['members'] = list_members_from_card(c)
        card['unplanned'] = is_card_unplanned(c)
        for cf in c.custom_fields:
            if cf.name.upper() == FIELD_BUGZILLA:
                card['bugzilla'] = cf.value
        card['name'] = c.name

        # Append to the planned or unplanned lists
        key = 'unplanned' if card['unplanned'] else 'planned'
        cards[key].append(card)

    return cards


def percentage(part, whole):
    try:
        return 100 * float(part)/float(whole)
    except ZeroDivisionError:
        return 100


def print_card(card, print_unplanned=False):
    print('\t*', card['name'],
          '[unplanned]' if print_unplanned and card['unplanned'] else '')
    if _INCLUDE_MEMBERS:
        print('\t\t[', ', '.join(card['members']), ']')


def print_report(lists):
    sprint_backlog_cards = parse_cards_from_list(lists, 'Sprint Backlog')
    doing_cards = parse_cards_from_list(lists, 'Doing')
    in_review_cards = parse_cards_from_list(lists, 'In Review')
    done_cards = parse_cards_from_list(lists, 'Done')

    units_planned_done = len(done_cards['planned'])
    units_unplanned_done = len(done_cards['unplanned'])

    units_planned = (len(sprint_backlog_cards['planned']) +
                     len(doing_cards['planned']) +
                     len(in_review_cards['planned']) +
                     units_planned_done)
    units_unplanned = (len(sprint_backlog_cards['unplanned']) +
                       len(doing_cards['unplanned']) +
                       len(in_review_cards['unplanned']) +
                       units_unplanned_done)

    print('Units of work planned:', units_planned)
    print('Units of work unplanned:', units_unplanned)
    print('Units of planned work achieved: %d (%.1f%%)' % (
        units_planned_done,
        percentage(units_planned_done, units_planned)))
    print('Units of unplanned work achieved: %d (%.1f%%)' % (
        units_unplanned_done,
        percentage(units_unplanned_done, units_unplanned)))

    print('Achievement Headline: ')
    for c in done_cards['planned']:
        print_card(c)

    print('Unplanned Headline: ')
    for c in done_cards['unplanned']:
        print_card(c)

    print('Unfinished cards: ')
    for c in (sprint_backlog_cards['planned'] +
              sprint_backlog_cards['unplanned'] +
              doing_cards['planned'] +
              doing_cards['unplanned'] +
              in_review_cards['planned'] +
              in_review_cards['unplanned']):
        print_card(c, print_unplanned=True)


def main():
    cli_options = get_cli_options()
    get_client(cli_options.config)
    board = get_board(cli_options.board)
    if not board:
        print('Board %s not found' % cli_options.board)
        return

    lists = board.list_lists('open')
    print_report(lists)


if __name__ == '__main__':
    main()
