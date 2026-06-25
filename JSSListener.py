# Generated from JSS.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .JSSParser import JSSParser
else:
    from JSSParser import JSSParser

# This class defines a complete listener for a parse tree produced by JSSParser.
class JSSListener(ParseTreeListener):

    # Enter a parse tree produced by JSSParser#program.
    def enterProgram(self, ctx:JSSParser.ProgramContext):
        pass

    # Exit a parse tree produced by JSSParser#program.
    def exitProgram(self, ctx:JSSParser.ProgramContext):
        pass


    # Enter a parse tree produced by JSSParser#topDecl.
    def enterTopDecl(self, ctx:JSSParser.TopDeclContext):
        pass

    # Exit a parse tree produced by JSSParser#topDecl.
    def exitTopDecl(self, ctx:JSSParser.TopDeclContext):
        pass


    # Enter a parse tree produced by JSSParser#functionDecl.
    def enterFunctionDecl(self, ctx:JSSParser.FunctionDeclContext):
        pass

    # Exit a parse tree produced by JSSParser#functionDecl.
    def exitFunctionDecl(self, ctx:JSSParser.FunctionDeclContext):
        pass


    # Enter a parse tree produced by JSSParser#params.
    def enterParams(self, ctx:JSSParser.ParamsContext):
        pass

    # Exit a parse tree produced by JSSParser#params.
    def exitParams(self, ctx:JSSParser.ParamsContext):
        pass


    # Enter a parse tree produced by JSSParser#param.
    def enterParam(self, ctx:JSSParser.ParamContext):
        pass

    # Exit a parse tree produced by JSSParser#param.
    def exitParam(self, ctx:JSSParser.ParamContext):
        pass


    # Enter a parse tree produced by JSSParser#classDecl.
    def enterClassDecl(self, ctx:JSSParser.ClassDeclContext):
        pass

    # Exit a parse tree produced by JSSParser#classDecl.
    def exitClassDecl(self, ctx:JSSParser.ClassDeclContext):
        pass


    # Enter a parse tree produced by JSSParser#classMember.
    def enterClassMember(self, ctx:JSSParser.ClassMemberContext):
        pass

    # Exit a parse tree produced by JSSParser#classMember.
    def exitClassMember(self, ctx:JSSParser.ClassMemberContext):
        pass


    # Enter a parse tree produced by JSSParser#constructorDecl.
    def enterConstructorDecl(self, ctx:JSSParser.ConstructorDeclContext):
        pass

    # Exit a parse tree produced by JSSParser#constructorDecl.
    def exitConstructorDecl(self, ctx:JSSParser.ConstructorDeclContext):
        pass


    # Enter a parse tree produced by JSSParser#methodDecl.
    def enterMethodDecl(self, ctx:JSSParser.MethodDeclContext):
        pass

    # Exit a parse tree produced by JSSParser#methodDecl.
    def exitMethodDecl(self, ctx:JSSParser.MethodDeclContext):
        pass


    # Enter a parse tree produced by JSSParser#attrDecl.
    def enterAttrDecl(self, ctx:JSSParser.AttrDeclContext):
        pass

    # Exit a parse tree produced by JSSParser#attrDecl.
    def exitAttrDecl(self, ctx:JSSParser.AttrDeclContext):
        pass


    # Enter a parse tree produced by JSSParser#type.
    def enterType(self, ctx:JSSParser.TypeContext):
        pass

    # Exit a parse tree produced by JSSParser#type.
    def exitType(self, ctx:JSSParser.TypeContext):
        pass


    # Enter a parse tree produced by JSSParser#castType.
    def enterCastType(self, ctx:JSSParser.CastTypeContext):
        pass

    # Exit a parse tree produced by JSSParser#castType.
    def exitCastType(self, ctx:JSSParser.CastTypeContext):
        pass


    # Enter a parse tree produced by JSSParser#block.
    def enterBlock(self, ctx:JSSParser.BlockContext):
        pass

    # Exit a parse tree produced by JSSParser#block.
    def exitBlock(self, ctx:JSSParser.BlockContext):
        pass


    # Enter a parse tree produced by JSSParser#statement.
    def enterStatement(self, ctx:JSSParser.StatementContext):
        pass

    # Exit a parse tree produced by JSSParser#statement.
    def exitStatement(self, ctx:JSSParser.StatementContext):
        pass


    # Enter a parse tree produced by JSSParser#varDecl.
    def enterVarDecl(self, ctx:JSSParser.VarDeclContext):
        pass

    # Exit a parse tree produced by JSSParser#varDecl.
    def exitVarDecl(self, ctx:JSSParser.VarDeclContext):
        pass


    # Enter a parse tree produced by JSSParser#varDeclNoSemi.
    def enterVarDeclNoSemi(self, ctx:JSSParser.VarDeclNoSemiContext):
        pass

    # Exit a parse tree produced by JSSParser#varDeclNoSemi.
    def exitVarDeclNoSemi(self, ctx:JSSParser.VarDeclNoSemiContext):
        pass


    # Enter a parse tree produced by JSSParser#declarator.
    def enterDeclarator(self, ctx:JSSParser.DeclaratorContext):
        pass

    # Exit a parse tree produced by JSSParser#declarator.
    def exitDeclarator(self, ctx:JSSParser.DeclaratorContext):
        pass


    # Enter a parse tree produced by JSSParser#constDecl.
    def enterConstDecl(self, ctx:JSSParser.ConstDeclContext):
        pass

    # Exit a parse tree produced by JSSParser#constDecl.
    def exitConstDecl(self, ctx:JSSParser.ConstDeclContext):
        pass


    # Enter a parse tree produced by JSSParser#returnStmt.
    def enterReturnStmt(self, ctx:JSSParser.ReturnStmtContext):
        pass

    # Exit a parse tree produced by JSSParser#returnStmt.
    def exitReturnStmt(self, ctx:JSSParser.ReturnStmtContext):
        pass


    # Enter a parse tree produced by JSSParser#ifStmt.
    def enterIfStmt(self, ctx:JSSParser.IfStmtContext):
        pass

    # Exit a parse tree produced by JSSParser#ifStmt.
    def exitIfStmt(self, ctx:JSSParser.IfStmtContext):
        pass


    # Enter a parse tree produced by JSSParser#elseClause.
    def enterElseClause(self, ctx:JSSParser.ElseClauseContext):
        pass

    # Exit a parse tree produced by JSSParser#elseClause.
    def exitElseClause(self, ctx:JSSParser.ElseClauseContext):
        pass


    # Enter a parse tree produced by JSSParser#whileStmt.
    def enterWhileStmt(self, ctx:JSSParser.WhileStmtContext):
        pass

    # Exit a parse tree produced by JSSParser#whileStmt.
    def exitWhileStmt(self, ctx:JSSParser.WhileStmtContext):
        pass


    # Enter a parse tree produced by JSSParser#forStmt.
    def enterForStmt(self, ctx:JSSParser.ForStmtContext):
        pass

    # Exit a parse tree produced by JSSParser#forStmt.
    def exitForStmt(self, ctx:JSSParser.ForStmtContext):
        pass


    # Enter a parse tree produced by JSSParser#forInit.
    def enterForInit(self, ctx:JSSParser.ForInitContext):
        pass

    # Exit a parse tree produced by JSSParser#forInit.
    def exitForInit(self, ctx:JSSParser.ForInitContext):
        pass


    # Enter a parse tree produced by JSSParser#breakStmt.
    def enterBreakStmt(self, ctx:JSSParser.BreakStmtContext):
        pass

    # Exit a parse tree produced by JSSParser#breakStmt.
    def exitBreakStmt(self, ctx:JSSParser.BreakStmtContext):
        pass


    # Enter a parse tree produced by JSSParser#exprStmt.
    def enterExprStmt(self, ctx:JSSParser.ExprStmtContext):
        pass

    # Exit a parse tree produced by JSSParser#exprStmt.
    def exitExprStmt(self, ctx:JSSParser.ExprStmtContext):
        pass


    # Enter a parse tree produced by JSSParser#expr.
    def enterExpr(self, ctx:JSSParser.ExprContext):
        pass

    # Exit a parse tree produced by JSSParser#expr.
    def exitExpr(self, ctx:JSSParser.ExprContext):
        pass


    # Enter a parse tree produced by JSSParser#assignOp.
    def enterAssignOp(self, ctx:JSSParser.AssignOpContext):
        pass

    # Exit a parse tree produced by JSSParser#assignOp.
    def exitAssignOp(self, ctx:JSSParser.AssignOpContext):
        pass


    # Enter a parse tree produced by JSSParser#orExpr.
    def enterOrExpr(self, ctx:JSSParser.OrExprContext):
        pass

    # Exit a parse tree produced by JSSParser#orExpr.
    def exitOrExpr(self, ctx:JSSParser.OrExprContext):
        pass


    # Enter a parse tree produced by JSSParser#andExpr.
    def enterAndExpr(self, ctx:JSSParser.AndExprContext):
        pass

    # Exit a parse tree produced by JSSParser#andExpr.
    def exitAndExpr(self, ctx:JSSParser.AndExprContext):
        pass


    # Enter a parse tree produced by JSSParser#cmpExpr.
    def enterCmpExpr(self, ctx:JSSParser.CmpExprContext):
        pass

    # Exit a parse tree produced by JSSParser#cmpExpr.
    def exitCmpExpr(self, ctx:JSSParser.CmpExprContext):
        pass


    # Enter a parse tree produced by JSSParser#cmpOp.
    def enterCmpOp(self, ctx:JSSParser.CmpOpContext):
        pass

    # Exit a parse tree produced by JSSParser#cmpOp.
    def exitCmpOp(self, ctx:JSSParser.CmpOpContext):
        pass


    # Enter a parse tree produced by JSSParser#addExpr.
    def enterAddExpr(self, ctx:JSSParser.AddExprContext):
        pass

    # Exit a parse tree produced by JSSParser#addExpr.
    def exitAddExpr(self, ctx:JSSParser.AddExprContext):
        pass


    # Enter a parse tree produced by JSSParser#mulExpr.
    def enterMulExpr(self, ctx:JSSParser.MulExprContext):
        pass

    # Exit a parse tree produced by JSSParser#mulExpr.
    def exitMulExpr(self, ctx:JSSParser.MulExprContext):
        pass


    # Enter a parse tree produced by JSSParser#powExpr.
    def enterPowExpr(self, ctx:JSSParser.PowExprContext):
        pass

    # Exit a parse tree produced by JSSParser#powExpr.
    def exitPowExpr(self, ctx:JSSParser.PowExprContext):
        pass


    # Enter a parse tree produced by JSSParser#unaryExpr.
    def enterUnaryExpr(self, ctx:JSSParser.UnaryExprContext):
        pass

    # Exit a parse tree produced by JSSParser#unaryExpr.
    def exitUnaryExpr(self, ctx:JSSParser.UnaryExprContext):
        pass


    # Enter a parse tree produced by JSSParser#postfixExpr.
    def enterPostfixExpr(self, ctx:JSSParser.PostfixExprContext):
        pass

    # Exit a parse tree produced by JSSParser#postfixExpr.
    def exitPostfixExpr(self, ctx:JSSParser.PostfixExprContext):
        pass


    # Enter a parse tree produced by JSSParser#argList.
    def enterArgList(self, ctx:JSSParser.ArgListContext):
        pass

    # Exit a parse tree produced by JSSParser#argList.
    def exitArgList(self, ctx:JSSParser.ArgListContext):
        pass


    # Enter a parse tree produced by JSSParser#primary.
    def enterPrimary(self, ctx:JSSParser.PrimaryContext):
        pass

    # Exit a parse tree produced by JSSParser#primary.
    def exitPrimary(self, ctx:JSSParser.PrimaryContext):
        pass



del JSSParser