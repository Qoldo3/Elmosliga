# Generated migration for points system and prediction updates

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('League', '0002_rename_first_place_prediction_first_place_team_and_more'),
    ]

    operations = [
        # Add points fields to League
        migrations.AddField(
            model_name='league',
            name='first_place_points',
            field=models.IntegerField(default=10),
        ),
        migrations.AddField(
            model_name='league',
            name='second_place_points',
            field=models.IntegerField(default=5),
        ),
        migrations.AddField(
            model_name='league',
            name='third_place_points',
            field=models.IntegerField(default=3),
        ),
        
        # Add second and third place back to Prediction
        migrations.AddField(
            model_name='prediction',
            name='second_place_team',
            field=models.ForeignKey(
                null=True,  # Temporarily allow null for migration
                on_delete=django.db.models.deletion.CASCADE,
                related_name='second_place_predictions',
                to='League.team'
            ),
        ),
        migrations.AddField(
            model_name='prediction',
            name='third_place_team',
            field=models.ForeignKey(
                null=True,  # Temporarily allow null for migration
                on_delete=django.db.models.deletion.CASCADE,
                related_name='third_place_predictions',
                to='League.team'
            ),
        ),
        
        # Add updated_at to Prediction
        migrations.AddField(
            model_name='prediction',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        
        # Update LeagueResult related_name to avoid conflicts
        migrations.AlterField(
            model_name='leagueresult',
            name='first_place',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='first_place_results',
                to='League.team'
            ),
        ),
        migrations.AlterField(
            model_name='leagueresult',
            name='second_place',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='second_place_results',
                to='League.team'
            ),
        ),
        migrations.AlterField(
            model_name='leagueresult',
            name='third_place',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='third_place_results',
                to='League.team'
            ),
        ),
    ]