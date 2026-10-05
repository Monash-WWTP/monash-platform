import 'package:flutter/material.dart';
import '../services/account_session.dart';
import '../services/platform_api.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});
  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: AccountSession.instance,
    builder: (context, _) => ListView(padding:const EdgeInsets.all(16),children:[
      const CircleAvatar(radius:36,child:Icon(Icons.person)),
      const SizedBox(height:16),
      Text(AccountSession.instance.signedIn ? 'Signed in to Monash Water' : 'Sign in to submit reports',
        textAlign:TextAlign.center,style:Theme.of(context).textTheme.titleMedium),
      const SizedBox(height:16),
      const Text('Use the same verified account as the dashboard. Citizen accounts do not grant operator access.'),
      if (AccountSession.instance.signedIn)
        FutureBuilder<dynamic>(future:PlatformApi().request('/api/v1/auth/me'),builder:(context,snapshot)=>
          ListTile(title:Text(snapshot.data?['email'] ?? 'Loading account…'))),
      FilledButton(onPressed:() async {
        try {
          if (AccountSession.instance.signedIn) { await AccountSession.instance.signOut(); }
          else { await AccountSession.instance.signIn(); }
        } catch (_) {
          if(context.mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Account service unavailable. Please try again.')));
        }
      },child:Text(AccountSession.instance.signedIn ? 'Sign out' : 'Sign in')),
      const Card(child:ListTile(title:Text('About CitizenFlood'),subtitle:Text('Record your observations. Approved public locations are rounded for privacy. Reports are community observations, not laboratory measurements.'))),
    ]));
}
