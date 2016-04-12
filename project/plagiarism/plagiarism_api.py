from plagiarism_utils import QueryExecutor
from plagiarismstructs import PlagiarismSubJob, PlagiarismTestingJob
from storage.storage import ResourceId
from django.db import transaction

executor = QueryExecutor()

def _make_job_field(id, res):
    return PlagiarismSubJob(id, res)

def _make_job(solution, solutions):
    return PlagiarismTestingJob(_make_job_field(solution['id'], solution['resource']),
        [_make_job_field(item['id'], item['resource']) for item in solutions])

def _res_to_hex_str(binary_resource):
    return str(ResourceId(str(binary_resource)))

def get_testing_job():
    get_job_query = ("SELECT solution_id,problem_id,author_id,reception_time,resource_id FROM"
        " (SELECT * FROM (SELECT * FROM solutions_judgement as J JOIN solutions_solution as S ON j.solution_id == s.id WHERE j.outcome == 1)"
        " as A JOIN storage_filemetadata as B ON A.source_code_id == B.id) WHERE solution_id NOT IN (SELECT id_id FROM plagiarism_aggregatedresult) ORDER BY reception_time LIMIT 1;")
    
    items = list(executor.get(get_job_query))
    if not items:
        return None

    sol_id,problem_id,author_id,dt,res = items[0]
    solution = { 'id' : sol_id, 'resource' : _res_to_hex_str(res) }

    get_previous_jobs = ("SELECT A.id,resource_id FROM"
        " (SELECT * FROM solutions_solution WHERE id IN (SELECT solution_id FROM solutions_judgement WHERE outcome == 1)"
        " AND problem_id == ? AND reception_time < ? AND author_id != ?) as A LEFT JOIN storage_filemetadata as B ON A.source_code_id == B.id;") 

    solutions = [{ 'id' : s_id, 'resource' : _res_to_hex_str(r) } for s_id, r in executor.get(get_previous_jobs, [problem_id, dt, author_id])]

    return _make_job(solution, solutions)

def _create_judgementresult_insert(data):
    sql = "INSERT INTO plagiarism_judgementresult (solution_to_judge_id,solution_to_compare_id,algo_id_id,similarity,verdict) VALUES "
    vals = []
    first = True
    for _ in data['comparasion']:
        for __ in _['result']['results']:
            if not first:
                sql += ', '
            first = False
            sql += "(?, ?, ?, ?, ?)"
            vals.extend([data['id'], _['id'], __['algo_id'], __['similarity'], __['verdict']])
            
    return (sql,vals)

def dump_plagiarism_report(data):
    print "checking: ", data['id']
    with transaction.atomic():
        if len(data['comparasion']) > 0:
           query, vals = _create_judgementresult_insert(data)
           executor.put(query, vals)
        
        dump_agg_templ = ("INSERT INTO plagiarism_aggregatedresult VALUES (?,?)")
        executor.put(dump_agg_templ, [data['id'], data['plagiarism_level']])
