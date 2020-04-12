import csv
import six

from .models import (
    IcpcContestant,
    IcpcTeam,
)


def make_teams_csv(event):
    contestants_per_team = {}

    for contestant in IcpcContestant.objects.filter(team__coach__event=event):
        contestants_per_team.setdefault(contestant.team_id, []).append(contestant)

    fields = ['coach_email', 'coach_first_name', 'coach_last_name', 'university', 'team_name', 'participation_venue', 'participation_type']
    for i in range(3):
        for field in ['email', 'first_name', 'last_name', 'date_of_birth', 'study_program', 'program_start_year', 'graduation_year', 'sex']:
            fields.append('contestant_{}_{}'.format(i + 1, field))

    si = six.StringIO()
    writer = csv.DictWriter(si, fields)
    writer.writeheader()

    for team in IcpcTeam.objects.filter(coach__event=event).select_related('coach'):
        row = {
            'coach_email': team.coach.email,
            'coach_first_name': team.coach.first_name,
            'coach_last_name': team.coach.last_name,
            'university': team.coach.university,
            'team_name': team.name,
            'participation_venue': team.participation_venue,
            'participation_type': team.participation_type,
        }
        contestants = contestants_per_team.get(team.id, [])
        if len(contestants) != 3:
            continue

        for i, contestant in enumerate(contestants):
            subrow = {
                'email': contestant.email,
                'first_name': contestant.first_name,
                'last_name': contestant.last_name,
                'date_of_birth': six.text_type(contestant.date_of_birth),
                'study_program': contestant.study_program,
                'program_start_year': contestant.program_start_year,
                'graduation_year': contestant.graduation_year,
                'sex': contestant.sex,
            }
            for k, v in subrow.items():
                row['contestant_{}_{}'.format(i + 1, k)] = v

        recoded_row = {}
        for k, v in row.items():
            recoded_row[k] = six.text_type(v)

        writer.writerow(recoded_row)

    return si.getvalue()
