from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('League', '0005_remove_prediction_first_place_team_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='prediction',
            name='is_predicted',
            field=models.BooleanField(default=False),
        ),
    ]