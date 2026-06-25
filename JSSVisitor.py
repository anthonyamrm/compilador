# Generated from JSS.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .JSSParser import JSSParser
else:
    from JSSParser import JSSParser

# This class defines a complete generic visitor for a parse tree produced by JSSParser.

class JSSVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by JSSParser#program.
    def visitProgram(self, ctx:JSSParser.ProgramContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#topDecl.
    def visitTopDecl(self, ctx:JSSParser.TopDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#functionDecl.
    def visitFunctionDecl(self, ctx:JSSParser.FunctionDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#params.
    def visitParams(self, ctx:JSSParser.ParamsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#param.
    def visitParam(self, ctx:JSSParser.ParamContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#classDecl.
    def visitClassDecl(self, ctx:JSSParser.ClassDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#classMember.
    def visitClassMember(self, ctx:JSSParser.ClassMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#constructorDecl.
    def visitConstructorDecl(self, ctx:JSSParser.ConstructorDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#methodDecl.
    def visitMethodDecl(self, ctx:JSSParser.MethodDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#attrDecl.
    def visitAttrDecl(self, ctx:JSSParser.AttrDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#type.
    def visitType(self, ctx:JSSParser.TypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#castType.
    def visitCastType(self, ctx:JSSParser.CastTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#block.
    def visitBlock(self, ctx:JSSParser.BlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#statement.
    def visitStatement(self, ctx:JSSParser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#varDecl.
    def visitVarDecl(self, ctx:JSSParser.VarDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#varDeclNoSemi.
    def visitVarDeclNoSemi(self, ctx:JSSParser.VarDeclNoSemiContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#declarator.
    def visitDeclarator(self, ctx:JSSParser.DeclaratorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#constDecl.
    def visitConstDecl(self, ctx:JSSParser.ConstDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#returnStmt.
    def visitReturnStmt(self, ctx:JSSParser.ReturnStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#ifStmt.
    def visitIfStmt(self, ctx:JSSParser.IfStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#elseClause.
    def visitElseClause(self, ctx:JSSParser.ElseClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#whileStmt.
    def visitWhileStmt(self, ctx:JSSParser.WhileStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#forStmt.
    def visitForStmt(self, ctx:JSSParser.ForStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#forInit.
    def visitForInit(self, ctx:JSSParser.ForInitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#breakStmt.
    def visitBreakStmt(self, ctx:JSSParser.BreakStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#exprStmt.
    def visitExprStmt(self, ctx:JSSParser.ExprStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#expr.
    def visitExpr(self, ctx:JSSParser.ExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#assignOp.
    def visitAssignOp(self, ctx:JSSParser.AssignOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#orExpr.
    def visitOrExpr(self, ctx:JSSParser.OrExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#andExpr.
    def visitAndExpr(self, ctx:JSSParser.AndExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#cmpExpr.
    def visitCmpExpr(self, ctx:JSSParser.CmpExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#cmpOp.
    def visitCmpOp(self, ctx:JSSParser.CmpOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#addExpr.
    def visitAddExpr(self, ctx:JSSParser.AddExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#mulExpr.
    def visitMulExpr(self, ctx:JSSParser.MulExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#powExpr.
    def visitPowExpr(self, ctx:JSSParser.PowExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#unaryExpr.
    def visitUnaryExpr(self, ctx:JSSParser.UnaryExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#postfixExpr.
    def visitPostfixExpr(self, ctx:JSSParser.PostfixExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#argList.
    def visitArgList(self, ctx:JSSParser.ArgListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by JSSParser#primary.
    def visitPrimary(self, ctx:JSSParser.PrimaryContext):
        return self.visitChildren(ctx)



del JSSParser