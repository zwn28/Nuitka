#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit patches or make the software available to licensors of
#     this software in either form, you automatically them grant them a
#     license for your part of the code under "Apache License 2.0" unless you
#     choose to remove this notice.
#
#     Kay Hayen uses the right to license his code under only GPL version 3,
#     to discourage a fork of Nuitka before it is "finished". He will later
#     make a new "Nuitka" release fully under "Apache License 2.0".
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#
""" Propagate exception raising upwards, maintaining side effects, and removing useless try constructs.

"""

from .OptimizeBase import OptimizationVisitorBase

from ..TreeOperations import RestartVisit

from nuitka.nodes.NodeMakingHelpers import (
    convertRaiseExceptionExpressionRaiseExceptionStatement,
    makeStatementsSequenceReplacementNode
)

class OptimizeRaisesVisitor( OptimizationVisitorBase ):
    def onEnterNode( self, node ):
        if node.isExpressionRaiseException():
            if node.parent.isStatementPrint():
                self.trimEvaluation(
                    node = node.parent
                )
            elif node.parent.isOperation():
                self.trimEvaluation(
                    node = node.parent
                )
            elif node.parent.isExpressionFunctionCall():
                self.trimEvaluation(
                    node = node.parent
                )
            elif node.parent.isStatementExpressionOnly():
                self.trimEvaluation(
                    node = node.parent
                )
            elif node.parent.isStatementRaiseException():
                self.trimEvaluation(
                    node = node.parent
                )
        elif node.isStatementRaiseException():
            if node.parent.isStatementsSequence():
                statements = node.parent.getStatements()

                if node is not statements[-1]:
                    node.parent.trimStatements( node )
                    statements = node.parent.getStatements()

                    self.signalChange(
                        "new_raise new_statements",
                        node.getSourceReference(),
                        "Removed unreachable statements from statement sequence."
                    )

                    raise RestartVisit

                if node.parent.parent.isStatementTryExcept():
                    if node is statements[0]:
                        for handler in node.parent.parent.getExceptionHandlers():
                            match = self.matchesException(
                                catched_exceptions = handler.getExceptionTypes(),
                                raised_exception   = node.getExceptionType()
                            )

                            if match is True:
                                return

                                # TODO: Make this robust and working again.

                                handler_target = handler.getExceptionTarget()

                                if handler_target is not None:
                                    exception_type = node.getExceptionType()

                                    if exception_type.isExpressionBuiltinExceptionRef():
                                        pass

                                    assert exception_type is not None

                                    assign_node = CPythonStatementAssignment(
                                        expression = exception_type,
                                        targets    = ( handler.getExceptionTarget(), ),
                                        source_ref = handler.getSourceReference(),
                                    )

                                    new_node = makeStatementsSequenceReplacementNode(
                                        statements = ( assign_node, ) + handler.getExceptionBranch().getStatements(),
                                        node       = handler,
                                    )
                                else:
                                    new_node = handler.getExceptionBranch()

                                node.parent.parent.replaceWith( new_node )

                                self.signalChange(
                                    "new_raise new_statements",
                                    node.getSourceReference(),
                                    "Resolved known raise to exception branch execution."
                                )

                                raise RestartVisit

                                # assert False
                            elif match is False:
                                assert False




            else:
                pass

    def trimEvaluation( self, node ):
        old_children = node.getVisitableNodes()
        new_children = []

        for child in old_children:
            new_children.append( child )

            if child.isExpressionRaiseException():
                break
        else:
            assert False

        side_effects = [ new_child for new_child in new_children[:-1] if new_child.mayHaveSideEffects() ]
        raise_exception = new_children[-1]

        if side_effects:
            raise_exception.addSideEffects( side_effects )

        if node.isExpression():
            node.replaceWith(
                new_node = raise_exception
            )

            self.signalChange(
                "new_raise",
                node.getSourceReference(),
                "Detected expression exception was propagated to expression upwards."
            )

            raise RestartVisit
        elif node.isStatement():
            node.replaceWith(
                new_node = convertRaiseExceptionExpressionRaiseExceptionStatement(
                    node = raise_exception
                )
            )

            self.signalChange(
                "new_raise new_statements",
                node.getSourceReference(),
                "Detected expression exception was converted to raise exception statement."
            )

            raise RestartVisit
        else:
            assert False

    def matchesException( self, catched_exceptions, raised_exception ):
        if catched_exceptions is None:
            return True

        # TODO: Why can raised_exception be None at all?
        if raised_exception is not None:
            for catched_exception in catched_exceptions:
                # Both are builtin exception references of the same name
                if catched_exception.isExpressionBuiltinExceptionRef() and \
                   raised_exception.isExpressionBuiltinExceptionRef():
                    # TODO: Could check run time objects from builtins for subclass relationship
                    if catched_exception.getExceptionName() == raised_exception.getExceptionName():
                        return True

                # Catched in builtin exception reference, and raised is an builtin one too.
                if catched_exception.isExpressionBuiltinExceptionRef() and \
                     raised_exception.isExpressionBuiltinMakeException():
                    # TODO: Could check run time objects from builtins for subclass relationship
                    if catched_exception.getExceptionName() == raised_exception.getExceptionName():
                        return True



        return None
