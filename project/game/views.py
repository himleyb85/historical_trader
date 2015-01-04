from django.views.generic import View
from django.utils.text import slugify
from django.shortcuts import render, redirect

from game.forms import GameCreateForm
from game.models import *

from portfolio.models import Stock_history, Holding
from portfolio.portfolio import Portfolio

import datetime
from pprint import pprint
from types import MethodType

def incrementer(time_span):
    if time_span == "weekly":
        return 7
    elif time_span == "monthly":
        return 30
    else:
        return 365

def get_game( game_id ):

    game = Whole_Game.objects.get( id=game_id )
    setattr( game, 'portfolio', Portfolio( game.portfolio_id ) )
    game.change_date( game.current_date )

    return game

class CreateGame( View ):
    def get( self, request ):
        request.context_dict['form'] = GameCreateForm()

        return render( request, 'game/index.html', request.context_dict )

    def post(self, request):
        form = GameCreateForm( request.POST )
        if form.is_valid():
            form_data = form.cleaned_data
            form_data['user'] = User.objects.get( id=request.user.id )

            portfolio_data = {
                'title': "game_{}".format( form_data['name'] ),
                'description': "Portfolio for game play.",
                'user': form_data['user']
            }

            portfolio = Portfolio.create( portfolio_data )

            form_data['portfolio_id'] = portfolio.id

            game = Whole_Game.objects.create( **form_data )
            return redirect( '/game/{}/start'.format( game.id ) )
        else:
            request.context_dict['form'] = form 
            return render( request, 'game/index.html', request.context_dict )


class UnfinishedGames( View ):
    def get(self, request):
        request.context_dict['games'] = Whole_Game.objects.filter(user=request.user, end_date=None)
        request.context_dict['starturl'] = "/game/{}/start"
        return render(request, 'game/find.html', request.context_dict)


class Start( View ):
    def get( self, request, game_id ):
        request.session.set_expiry(300)
        game = get_game( game_id )
        request.session['game_id'] = game_id
        return redirect( '/game/{}/manage'.format( game_id ) )


class Manage( View ):
    def get( self, request, game_id ):
        request.context_dict['game'] = get_game( game_id )

        return render( request, 'game/manage.html', request.context_dict )


class Manage_add( View ):
    def post( self, request, game_id ):
        request.context_dict['game'] = get_game( game_id )
        form = Portfolio.create_holding( request.POST )

        # logic here to make sure user can afford stocks
        if form.is_valid():
            form_data = form.cleaned_data
            form_data['date'] = str( request.context_dict['game'].current_date )

            form_data['price'] = request.context_dict['game'].portfolio.stock_by_date( form_data['symbol'] ).close

            results = request.context_dict['game'].portfolio.add_holding( form_data )

            request.context_dict['game'].balance -= results
            request.context_dict['game'].save( update_fields=["balance"] )

            return redirect( '/game/{}/manage'.format( game_id ) )

        else:
            request.context_dict[ 'form' ] = form

            return render( request, 'game/manage.html', request.context_dict )


class Manage_remove( View ):
    def post( self, request, game_id ):
        game = get_game( game_id )
        symbol = request.POST.get( 'symbol', None )
        amount = request.POST.get( 'amount', None )
        results = game.portfolio.remove_holding( symbol, amount )

        if results:
            game.balance += results
            game.save( update_fields=["balance"] )

            return redirect( '/game/{}/manage'.format( game_id ) )
        else:
            # add error here, but this should never be called?
            return redirect( '/game/{}/manage'.format( game_id ) )

# <<<<<<< HEAD
#not working, infinite loop
class RoundView( View ):
    def get(self, request, game_id):
        game = get_game( game_id )
        if game.total_rounds == game.current_round:
            return redirect( '/game/endgame')
        game.current_round += 1
        game.current_date += datetime.timedelta(days=incrementer(game.game_type))
#Just in case the current date lands on a weekend or holiday, here we check if 
#current date has stocks from that day, if not, increment by another day

        stocks = Stock_history.objects.all()
        print(stocks[0].date)
        print(game.current_date)
        while len(Stock_history.objects.first(date=game.current_date)) == None:
            pprint('IN DA LOOOOOOP')
            game.current_date += datetime.timedelta(days=1)
        pprint("HERE YET?")     
        game.save( update_fields=["current_date", "current_round"] )   
        return redirect( '/game/{}/manage'.format( game_id ) )
# =======
# class NextRoundView( View ):
#     template_name = 'game/round.html'
# # the round is incremented by 1 every round, but the date could be incremented by 7 days, 30 days, or 365 days
# # which actually doesn't work because it doesn't account for leap years, months not 30 days long and most importantly, THE USER CAN ONLY ACTUALLY PLAY ON WEEKDAYS NOT WEEKENDS OR HOLIDAYS
# # get should be used at the beginning of the first round.  Here the request.session variables should be set
#     def get(self, request, game_id):
#         game = get_game( game_id )
#         if game.current_round < game.total_rounds:
#             print(game.current_round)
#             game.current_round += 1
#             increment = incrementer(game.game_type)
#             days = game.current_round * increment
#             start = game.current_date
#             print(start.strftime("%A"))
#             time = datetime.timedelta(days=increment)
#             end = start + time
#             game.current_date = end
#             game.save(update_fields=['current_round', 'current_date'])
#             print(game.current_date)
#             search_start = end - datetime.timedelta(days=increment)
#             stocks = Stock_history.objects.filter(date__range=[search_start, end])
#             return render( request, self.template_name, { 'stocks':stocks, 'game':game } )
#         else:
#             return render(request, 'results.html')
# #everything else in the round should happen in a post except the initial setting of session variables in get
#     def post(self, request):
#         pass


# class CurrentRoundView( View ):
#     template_name = 'game/round.html'
# # the round is incremented by 1 every round, but the date could be incremented by 7 days, 30 days, or 365 days
# # which actually doesn't work because it doesn't account for leap years, months not 30 days long and most importantly, THE USER CAN ONLY ACTUALLY PLAY ON WEEKDAYS NOT WEEKENDS OR HOLIDAYS
# # get should be used at the beginning of the first round.  Here the request.session variables should be set
#     def get(self, request, game_id):
#         game = get_game( game_id )
#         increment = incrementer(game.game_type)
#         days = game.current_round * increment
#         start = game.current_date
#         time = datetime.timedelta(days=increment)
#         end = start + time
#         search_start = end - datetime.timedelta(days=increment)
#         stocks = Stock_history.objects.filter(date__range=[search_start, end])
#         return render(request, self.template_name, {'stocks':stocks, 'game':game})


# class UnfinishedGames( View ):
#     template_name = 'game/find.html'

#     def get(self, request):
#         request.context_dict['games'] = Whole_Game.objects.filter(user=request.user, end_date=None)
#         request.context_dict['starturl'] = "/game/{}/start"
#         return render(request, self.template_name, request.context_dict)
# >>>>>>> 6f29913cf78b51d9cb41c20c17d35838b8413deb

class StatsView( View ):
    template_name = 'game/stats.html'

    def get(self, request):
        if request.session['game_type'] == 'weekly':
                days = request.session['round']*7
                start = datetime.datetime.strptime(request.session['start_date'],"%Y-%m-%d")
                time = datetime.timedelta(days=days)
                end = start + time
                search_start = end - datetime.timedelta(days=7)
                stocks = Stock_history.objects.filter(date__range=[search_start, end])
                game = Whole_Game.objects.get(id=request.session['game_id'])
                return render(request, self.template_name, {'stocks':stocks, 'game':game})
        elif request.session['game_type'] == 'monthly':
            days = request.session['round']*31
            start = datetime.datetime.strptime(request.session['start_date'],"%Y-%m-%d")
            time = datetime.timedelta(days=days)
            end = start + time
            search_start = end - datetime.timedelta(days=31)
            request.session['search_start'] = search_start
            request.session['current_date'] = end
            stocks = Stock.objects.filter(date__range=[search_start, end])
            return render(request, self.template_name, {'stocks':stocks})
        elif request.session['game_type'] == 'yearly':
            days = request.session['round']*365
            start = datetime.datetime.strptime(request.session['start_date'],"%Y-%m-%d")
            time = datetime.timedelta(days=days)
            end = start + time
            search_start = end - datetime.timedelta(days=365)
            request.session['search_start'] = search_start
            request.session['current_date'] = end
            stocks = Stock.objects.filter(date__range=[search_start, end])
            return render(request, self.template_name, {'stocks':stocks})
        else:
            pass

class Leaderboard(View):
    def get(self, request):
        if request.user.is_anonymous():
            return redirect( '/')
        else:
            request.context_dict['games'] = Whole_Game.objects.filter(user=request.user)
            request.context_dict['highscores'] = Whole_Game.objects.all().order_by('final_score')[:9]
            return render( request, 'game/profile.html', request.context_dict)


class EndGame( View ):
    def get(self, request):
#first, sell all the shares in the portfolio
#then display final score and other stuff
        return render (request, 'game/endgame.html', request.context_dict)
