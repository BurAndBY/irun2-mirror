from django.db import models
from django.db.models.fields.related import ForeignObject
from django.db.models.options import Options
from django.db.models.sql.datastructures import Join
from django.db.models.sql.constants import INNER

# See
# https://stackoverflow.com/questions/22902263/django-orm-joining-subquery
# https://stackoverflow.com/questions/21271835/left-join-django-orm


class CustomJoin(Join):
    def __init__(self, subquery, subquery_params, parent_alias, table_alias, join_type, join_field, nullable):
        self.subquery_params = subquery_params
        super(CustomJoin, self).__init__(subquery, parent_alias, table_alias, join_type, join_field, nullable)

    def as_sql(self, compiler, connection):
        """
        Generates the full
        LEFT OUTER JOIN (somequery) alias ON alias.somecol = othertable.othercol, params
        clause for this join.
        """
        params = []
        sql = []
        alias_str = '' if self.table_alias == self.table_name else (' %s' % self.table_alias)
        params.extend(self.subquery_params)
        qn = compiler.quote_name_unless_alias
        qn2 = connection.ops.quote_name
        sql.append('%s (%s)%s ON (' % (self.join_type, self.table_name, alias_str))
        for index, (lhs_col, rhs_col) in enumerate(self.join_cols):
            if index != 0:
                sql.append(' AND ')
            sql.append('%s.%s = %s.%s' % (
                qn(self.parent_alias),
                qn2(lhs_col),
                qn(self.table_alias),
                qn2(rhs_col),
            ))
        extra_cond = self.join_field.get_extra_restriction(
            compiler.query.where_class, self.table_alias, self.parent_alias)
        if extra_cond:
            extra_sql, extra_params = compiler.compile(extra_cond)
            extra_sql = 'AND (%s)' % extra_sql
            params.extend(extra_params)
            sql.append('%s' % extra_sql)
        sql.append(')')
        return ' '.join(sql), params


def join_to(table, subquery, table_field, subquery_field, queryset, alias):
    """
    Add a join on `subquery` to `queryset` (having table `table`).
    """
    # here you can set complex clause for join
    def extra_join_cond(where_class, alias, related_alias):
        return None

    foreign_object = ForeignObject(to=subquery, from_fields=[None], to_fields=[None], rel=None, on_delete=models.CASCADE)
    foreign_object.opts = Options(table._meta)
    foreign_object.opts.model = table
    foreign_object.get_joining_columns = lambda: ((table_field, subquery_field),)
    foreign_object.get_extra_restriction = extra_join_cond
    subquery_sql, subquery_params = subquery.query.sql_with_params()
    join = CustomJoin(
        subquery_sql,
        subquery_params,
        table._meta.db_table,
        alias,
        INNER,
        foreign_object,
        False
    )

    # HACK: fills aliases
    str(queryset.query)
    queryset.query.join(join)

    # hook for set alias
    join.table_alias = alias
    queryset.query.external_aliases.add(alias)

    return queryset
