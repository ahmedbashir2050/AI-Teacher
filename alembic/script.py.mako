"""A mako template for creating Alembic migration scripts.

This template is used by the `alembic revision` command to generate
a new migration script.

"""
from alembic.runtime.migration import RevisionStep
from alembic.util import as_revision, rev_id
from textwrap import dedent
import logging

log = logging.getLogger(__name__)


def create_script(script):
    """Create a new migration script."""

    script.revision = rev_id()
    script.down_revision = as_revision("base")
    script.message = "New migration"
    script.branch_labels = None
    script.path = "versions/%s.py" % script.revision

    upgrades = []
    downgrades = []

    for step in script.generate_template_args()["upgrades"]:
        if isinstance(step, RevisionStep):
            upgrades.append(
                dedent(
                    """\
    op.create_table(
        '%(table_name)s',
    %(table_args)s
    )"""
                )
                % {
                    "table_name": step.table_name,
                    "table_args": ",\n".join(
                        [
                            "    sa.Column('%s', sa.%s, nullable=%s),"
                            % (
                                col.name,
                                col.type.__class__.__name__,
                                col.nullable,
                            )
                            for col in step.columns
                        ]
                    ),
                }
            )
        else:
            log.warning("Ignoring step %r", step)

    for step in script.generate_template_args()["downgrades"]:
        if isinstance(step, RevisionStep):
            downgrades.append(
                "    op.drop_table('%(table_name)s')" % {"table_name": step.table_name}
            )
        else:
            log.warning("Ignoring step %r", step)

    script.upgrades = "\n".join(upgrades)
    script.downgrades = "\n".join(downgrades)

    return script
